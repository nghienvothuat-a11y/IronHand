IRONHAND MK1 — BẢN MODEL VÀ RIG PROTOTYPE
Ngày: 04/10/2026

FILE CHÍNH
IronHand_MK1_Rigged.blend: bản chỉnh sửa, có mesh gốc ẩn để đối chiếu.
../../assets/exports/IronHand_MK1_Rigged.fbx: mesh, skeleton và animation đã bake.
../../assets/exports/IronHand_MK1_Rigged.glb: bản trao đổi có texture nhúng.
../../assets/exports/IronHand_MK1_RigContract.json: tên xương, controls và mapping
21 landmark để chuẩn bị retargeting. Mapping này chưa phải code hand tracking.
../../assets/source/IronHand_MK1_Tripo_Source.fbx: file gốc tải từ Tripo, giữ nguyên.

XEM TRONG BLENDER
Mở IronHand_MK1_Rigged.blend. Đưa chuột vào viewport và nhấn Space để chạy/dừng
animation thử dài 180 frame, 30 fps. Các mốc: 1 xoè tay; 25 thả lỏng; 55 nắm;
85 xoè; 110 co ngón trỏ; 135 xoè; 160 thử pinch; 180 xoè.
Để chỉnh tay trực tiếp, bỏ gán action IronHand_Gesture_Demo khỏi IronHand_Rig,
rồi chỉnh Object Properties > Custom Properties:
  thumb_curl, index_curl, middle_curl, ring_curl, little_curl: 0–1.
  thumb_opposition: 0–1, xoay ngón cái về phía lòng bàn tay.
  wrist_pitch, wrist_yaw: -1–1.
Giữ action sẽ khiến các giá trị được animation ghi lại khi đổi frame.
Viewport mặc định ẩn overlays cho dễ xem vật liệu; bật Show Overlays để thấy rig.

THÔNG SỐ
Một skinned mesh; một material; 7.838 vertex / 14.470 triangle ở mesh Blender.
23 xương tổng cộng, gồm root và marker đầu ngón không biến dạng.
Đơn vị mét, chiều dài cả tay và cuff khoảng 0,280 m, gốc cổ tay tại (0,0,0).
Trong Blender: ngón hướng +Z, pháp tuyến lòng bàn tay hướng -Y.
Palm_Muzzle là empty gắn với xương Hand.R để đặt hiệu ứng phát bắn.
Hướng bắn gameplay vẫn phải do bộ ngắm/retargeting quyết định.

VẬT LIỆU
Mesh Tripo tải về không có UV/texture. Bản này có UV theo bảng màu dùng chung
và bộ texture 256x256 tự tạo trong Blender: BaseColor, ORM và Emission.
ORM: R=AO, G=roughness, B=metallic. Đây không phải texture atlas riêng từng mặt
để vẽ chi tiết. Chưa có normal map bake. Texture đã pack trong .blend và .glb.
Khi dựng material URP phải chuyển cách đóng gói kênh phù hợp shader được chọn;
không gán thẳng ORM vào một slot metallic/smoothness khác quy ước.

KIỂM TRA ĐÃ LÀM
Xem rig-validation.json: trọng số cứng mỗi vertex, không có polygon chịu nhiều
xương, ngón trỏ chuyển động độc lập, chiều dài cạnh giáp giữ nguyên khi nắm,
tỷ lệ mét, vị trí Palm_Muzzle; nhập lại FBX kiểm tra skin/xương/animation;
kiểm tra cấu trúc GLB có skin, animation và image nhúng.
Ảnh open/fist/index-curl/pinch trong ../previews là render trực tiếp từ Blender.

GIỚI HẠN CẦN LÀM TIẾP
Đây là rig cơ khí để thử prototype. Mesh AI còn cạnh giáp gồ ghề, khe tại gốc
ngón và khả năng xuyên nhau khi ép tư thế mạnh; cần chỉnh khi chốt thiết kế.
Vị trí khớp được fit theo model, chưa hiệu chỉnh theo bàn tay thật của người chơi.
Pose pinch chỉ là pose kiểm tra; không phải thuật toán nhận biết pinch.
Chưa nhập vào Unity, chưa thử tracking, occlusion hay FPS trên iPhone 13 Pro Max.
Chưa có retargeting realtime, VFX bắn, quái vật hoặc vòng lặp gameplay.

NGUỒN VÀ TRẠNG THÁI
Tripo task: 56f4080d-c961-4023-9d9c-b53baca28ca2
https://studio.tripo3d.ai/workspace/generate/56f4080d-c961-4023-9d9c-b53baca28ca2
Người dùng đã nâng cấp tài khoản và FBX đã xuất thành công. Ghi chú bị chặn
export trong tài liệu kế hoạch trước đó mô tả trạng thái trước khi nâng cấp.
Không phát sinh lần generate Tripo mới trong bước export/rig này.

TÁI TẠO VÀ KIỂM TRA
Từ thư mục dự án, chạy Blender background với tools/build_hand_rig.py,
sau đó tools/validate_hand_rig.py. Script hiện dùng đường dẫn dự án
/Users/mrk/IronHand; đổi biến R nếu chuyển sang máy/thư mục khác.
