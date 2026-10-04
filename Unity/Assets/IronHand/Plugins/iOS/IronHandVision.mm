#import <Foundation/Foundation.h>
#import <Vision/Vision.h>
#import <CoreGraphics/CoreGraphics.h>
#import <UIKit/UIKit.h>
#include <mutex>
#include <atomic>
#include <cstring>

namespace {
std::mutex gate;
std::atomic<bool> busy(false);
std::atomic<unsigned> generation(0);
float points[63] = {};
double captureTime = 0, elapsedMs = 0;
int result = 0, left = 0;
dispatch_queue_t queue() {
    static dispatch_queue_t q = dispatch_queue_create("com.ironhand.vision", DISPATCH_QUEUE_SERIAL);
    return q;
}
}
extern "C" int IH_Submit(const void* rgba,int width,int height,double capture) {
    if(!rgba || width<1 || height<1 || width>2048 || height>2048 || busy.exchange(true))return 0;
    unsigned ticket = generation.load();
    NSData* copy = [NSData dataWithBytes:rgba length:(NSUInteger)width*height*4];
    dispatch_async(queue(), ^{
        @autoreleasepool {
            CFTimeInterval start = CACurrentMediaTime();
            CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
            CGDataProviderRef provider = CGDataProviderCreateWithCFData((__bridge CFDataRef)copy);
            CGImageRef image = CGImageCreate(width,height,8,32,width*4,cs,kCGBitmapByteOrder32Big|kCGImageAlphaLast,provider,nullptr,false,kCGRenderingIntentDefault);
            VNDetectHumanHandPoseRequest* request = [VNDetectHumanHandPoseRequest new];
            request.maximumHandCount = 1;
            VNImageRequestHandler* handler = [[VNImageRequestHandler alloc] initWithCGImage:image orientation:kCGImagePropertyOrientationUp options:@{}];
            NSError* error = nil;
            BOOL ok = [handler performRequests:@[request] error:&error];
            float out[63] = {};
            int state = ok ? 2 : -1;
            int side = 0;
            VNHumanHandPoseObservation* hand = request.results.firstObject;
            if(ok && hand) {
                NSArray<VNHumanHandPoseObservationJointName>* names = @[
                    VNHumanHandPoseObservationJointNameWrist,
                    VNHumanHandPoseObservationJointNameThumbCMC,VNHumanHandPoseObservationJointNameThumbMP,VNHumanHandPoseObservationJointNameThumbIP,VNHumanHandPoseObservationJointNameThumbTip,
                    VNHumanHandPoseObservationJointNameIndexMCP,VNHumanHandPoseObservationJointNameIndexPIP,VNHumanHandPoseObservationJointNameIndexDIP,VNHumanHandPoseObservationJointNameIndexTip,
                    VNHumanHandPoseObservationJointNameMiddleMCP,VNHumanHandPoseObservationJointNameMiddlePIP,VNHumanHandPoseObservationJointNameMiddleDIP,VNHumanHandPoseObservationJointNameMiddleTip,
                    VNHumanHandPoseObservationJointNameRingMCP,VNHumanHandPoseObservationJointNameRingPIP,VNHumanHandPoseObservationJointNameRingDIP,VNHumanHandPoseObservationJointNameRingTip,
                    VNHumanHandPoseObservationJointNameLittleMCP,VNHumanHandPoseObservationJointNameLittlePIP,VNHumanHandPoseObservationJointNameLittleDIP,VNHumanHandPoseObservationJointNameLittleTip];
                for(int i=0;i<21;i++) {
                    VNRecognizedPoint* p = [hand recognizedPointForJointName:names[i] error:nil];
                    if(p){out[i*3]=p.x;out[i*3+1]=p.y;out[i*3+2]=p.confidence;}
                }
                if(@available(iOS 15.0,*))side=hand.chirality==VNChiralityLeft ? 1 : 0;
                state=1;
            }
            CGImageRelease(image);CGDataProviderRelease(provider);CGColorSpaceRelease(cs);
            {
                std::lock_guard<std::mutex> lock(gate);
                if(ticket==generation.load()){std::memcpy(points,out,sizeof(points));captureTime=capture;elapsedMs=(CACurrentMediaTime()-start)*1000;left=side;result=state;}
            }
            busy.store(false);
        }
    });
    return 1;
}
extern "C" int IH_Poll(float* xyz,double* capture,double* elapsed,int* handedness) {
    std::lock_guard<std::mutex> lock(gate);
    if(result==0)return 0;
    std::memcpy(xyz,points,sizeof(points));*capture=captureTime;*elapsed=elapsedMs;*handedness=left;
    int value=result;result=0;return value;
}
extern "C" void IH_Reset(){generation.fetch_add(1);std::lock_guard<std::mutex> lock(gate);result=0;}
extern "C" void IH_Haptic(){dispatch_async(dispatch_get_main_queue(), ^{static UIImpactFeedbackGenerator* h=nil;if(!h)h=[[UIImpactFeedbackGenerator alloc] initWithStyle:UIImpactFeedbackStyleLight];[h impactOccurredWithIntensity:.45f];});}
