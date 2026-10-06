THE EMPYREAN CAM RANH — NGOẠI THẤT THEO ẢNH
Bản sửa bốn tòa riêng biệt • 05/10/2026 • Blender 5.2

MỞ FILE
source/Empyrean_CamRanh_Exterior.blend là bản chính để chỉnh sửa và render.
Vật liệu ảnh đã được pack vào file. Camera, ánh sáng, cảnh quan và biển nằm sẵn trong scene.
Chọn camera 01 (nhìn từ đất liền), 02 (nhìn từ phía biển) hoặc 06 (góc biển đối diện).
Camera 07 chụp gần phần mái nối cong đã sửa hướng ra ngoài ở tòa thấp phía biển.
Các ảnh trong renders/ có kích thước 3000 × 2000, render bằng Cycles.
exports/Empyrean_Exterior_Core.glb là bản chuyển đổi dùng trong các phần mềm khác.

PHẠM VI
Chỉ dựng ngoại thất: bốn khối khách sạn, mặt đứng, ban công, các mái giật tầng,
khối mái cong thấp phía biển, khối thương mại thấp tầng, quảng trường, bể bơi,
đường, lối đi, cây xanh, bãi biển và mặt nước làm bối cảnh. Không có phòng nội thất.
Đây là mô hình phục vụ phối cảnh, chưa được tối ưu thành asset cho game di động.

BỐN KHỐI ĐƯỢC DỰNG RIÊNG
Tên A/B/C/D là mã vị trí trong mô hình, không khẳng định tên tòa chính thức.
+X hướng ra biển, +Y là hướng bắc quy ước của mô hình; chưa đăng ký tọa độ khảo sát.

A_Land_North: khối cao phía đất liền, mặt bằng U tương đối hẹp, đỉnh cao,
              hai cánh hạ tầng mạnh và không hoàn toàn đối xứng; viền màu đất nung.
B_Sea_North:  khối cao phía biển, chiều cao, độ xòe cánh và độ dài cánh riêng;
              viền xanh; sân bơi kéo dài ra biển và vòng sông lười khép kín.
C_Land_South: khối thấp phía đất liền, đường cong mở rộng, mái chính dài hơn,
              số tầng và nhịp giật tầng khác A/B; sân trong có bể bơi nhỏ.
D_Sea_South:  khối thấp phía biển, mặt bằng cong khác C, bể bơi tự do lớn hơn;
              có khối mái thấp uốn cong RA NGOÀI, rời sân hồ bơi ở đầu cánh.
              Đã sửa hướng cong theo ảnh Google Maps và sơ đồ resort; đường
              tiếp cận tại góc khu đất được nối lại để tránh xuyên qua mái nối.

Collection EMP_10_* tách riêng từng tòa. Mỗi tòa tách tiếp sàn, mặt đứng,
khung cửa, lan can, mái và phần sảnh để chỉnh độc lập.
EMP_20/30: hạ tầng và khối thương mại. EMP_40/45: cây xanh và tiện ích ngoài trời.
EMP_90: bối cảnh xa. EMP_99/80: camera và ánh sáng.

ĐỘ CHÍNH XÁC
Hình khối được đối chiếu từ hai ảnh Google Maps do người dùng cung cấp, ảnh
chụp trên website chính thức của khách sạn và ảnh toàn cảnh công khai.
Ưu tiên ảnh thực tế khi khác phối cảnh quảng bá, đặc biệt ở hai khối thấp.
Không dùng một tòa duy nhất rồi sao chép bốn lần.

Không có CAD, bản vẽ đo đạc hoặc bộ ảnh photogrammetry. Kích thước, tầng cao,
chiều dày cánh, nhiều chi tiết mái và vị trí cây là ước lượng phục vụ dựng hình.
Các giá trị tầng 25/21/12/10 trong parameters.json là lựa chọn dựng hình,
KHÔNG phải số tầng công trình đã được xác minh. Biển, khu đất xung quanh và
cây bối cảnh được diễn giải, không phải tái tạo địa hình đo đạc.
Đây là bản tái dựng theo ảnh, chưa phải bản sao số chính xác của công trình.

VẬT LIỆU VÀ NGUỒN
Ảnh tham chiếu không được chiếu lên mặt đứng làm texture.
Texture cát Aerial Beach 01: Rob Tuytel, Poly Haven, CC0.
Texture nền Leafy Grass: Charlotte Baglioni, Poly Haven, CC0.
Màu nền cỏ được chỉnh trong shader để phù hợp sân vườn được chăm sóc.
Danh sách URL và nguồn ảnh: references/reference_manifest.json.
Thông tin texture: source/textures/licenses.json.

KHÁC BIỆT GIỮA BLEND VÀ GLB
BLEND giữ toàn bộ shader Cycles, biển, nền xa, camera và ánh sáng.
GLB giữ lõi công trình và cảnh quan gần, bỏ nền xa/camera/ánh sáng.
Một số node thủ tục của Cycles không chuyển nguyên trạng sang glTF;
vật liệu nền cỏ ở GLB dùng màu cơ sở và các map chuyển được.
GLB là bản trao đổi hình học; dùng BLEND để ra phối cảnh như ảnh bàn giao.
Không có rig, animation, nội thất, collider hoặc LOD cho game.

KIỂM TRA ĐÃ THỰC HIỆN
Xuất GLB 2.0 và nhập ngược lại vào một phiên Blender sạch.
Kiểm tra bốn tòa, mái cong riêng của D, số node/mesh và tọa độ hữu hạn.
Chi tiết kiểm tra nằm ở qa/export_validation.json và qa/scene_audit.json.
Các ảnh cũ trong qa/ chỉ là bản nháp, không phải ảnh bàn giao.

MÃ NGUỒN DỰNG HÌNH
source/stages/ lưu các bước dựng có thể chỉnh tham số.
00_common.py: tham số mặt bằng riêng cho từng tòa.
11_towers_asbuilt.py: hình học bốn khối và mái cong D.
12_pavilion.py: phần mái nối D tách riêng, kiểm soát hướng cong độc lập.
20_site.py, 30_landscape.py: mặt bằng và cảnh quan.
40–80: camera, vật liệu, chi tiết và ánh sáng.
85_pavilion_clearance.py: dời các cây vướng phần mái nối và đường mới tại góc này.
10_towers.py là bản đầu đã bỏ, không chạy trong quy trình hiện tại.

tools/rebuild_scene.py chạy trong Blender nền sạch để dựng lại.
Đường dẫn root trong các script hiện trỏ đến thư mục này trên máy người dùng;
khi chuyển máy cần sửa ROOT/root ở các script. Chạy final_render.py sau khi
rebuild để áp lại cấu hình camera, màu và render cuối.

Ví dụ:
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/rebuild_scene.py

Không chạy rebuild trong phiên Blender đang chứa công việc khác.
File .blend hiện tại đã hoàn chỉnh cấu trúc scene và có thể mở trực tiếp,
không cần chạy lại các script để sử dụng.
