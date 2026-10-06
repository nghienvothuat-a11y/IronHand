THE EMPYREAN CAM RANH — NGOẠI THẤT V2 (DỰNG LẠI THEO FEEDBACK)
06/10/2026 • Blender 5.2 LTS • Cycles

MỞ FILE
source/Empyrean_CamRanh_Exterior_v2.blend là bản chính mới.
File cũ source/Empyrean_CamRanh_Exterior.blend được giữ nguyên để so sánh.
Texture trỏ tương đối tới source/textures/ (cần git lfs pull). Các pattern sinh riêng
(mosaic, ốp ô vuông shopvilla, pin mặt trời) được pack sẵn trong file.
Camera 01–09 có sẵn. Cài đặt render trong file: Cycles 3000 × 2000, 256 spp.
Ảnh trong renders/v2/ render bằng source/v2/render_cameras.py ở 2400 × 1600, 160 spp.
exports/Empyrean_Exterior_v2_Core.glb: công trình + mặt đất + hồ + tiện ích + bồn cây,
nén Draco, texture 1K. Không gồm cây/bụi (instance), nền 24 km và mặt biển.

XỬ LÝ TỪNG MỤC FEEDBACK
1. Mesh hở / khối bị tách rời
   File cũ: mọi mặt là quad rời (số vertex = 4 × số mặt) nên 100% cạnh hở.
   V2: mỗi tòa là MỘT lưới hàn liền; ô tường, cửa, sàn mái, tường bậc thang
   dùng chung vertex. Kiểm tra trong qa/v2_geometry_report.json:
   975 object, ~885k vertex, ~731k mặt, 0 cạnh biên, 0 cạnh non-manifold.
2. Cửa sổ không lõm vào trong
   Mỗi ô cửa là một inset thật: khung trên mặt tường, 4 mặt ô thoáng lùi vào,
   kính ở đáy, khung/đố nhôm là khối riêng. Cửa sổ đục lỗ lõm 0,22 m; logia ban
   công phía sân lõm 1,55 m; vách kính tầng 1 lõm 0,35 m. Tổng 8.150 ô cửa tháp.
3–4. Thiếu ban công, lan can, chi tiết cửa
   Ban công phía sân: sàn gạch, trần, lan can kính + tay vịn inox mỗi phòng.
   Sân thượng bậc thang hai cánh: lan can kính theo mép. Cánh mặt ngoài dạng
   răng cưa (mặt kính + mặt đặc màu be), dải mosaic ở mép sàn
   (Sea: xanh dương, Light: đất nung, Sand/Wind: xám). Kính có rèm ngẫu nhiên.
5. Tầng 1 và asset xung quanh
   Tầng 1 vách kính khung nhôm; sảnh lồi hình liềm phía sân; mái đón xe + cột,
   cột cờ, bảng tên. 228 đèn đường, 155 ghế hồ bơi + dù, 96 dù bãi biển,
   ghế đá quanh Arena, 2 mái che căng, 67 xe theo vị trí trên ảnh vệ tinh,
   bồn cây vuông dưới hàng cây trong khu shopvilla.
6. Độ cao và số tầng (Chứng nhận Kỷ lục Việt Nam 22/09/2023, kyluc.vn)
   Light (bắc, phía đất liền)  18 tầng + tầng mái  ~71 m (công bố 80 m)
   Sea   (bắc, sát biển)       20 tầng + tầng mái  ~78 m (công bố 79,2 m)
   Sand  (nam, phía biển)       8 tầng + tầng mái  ~32 m
   Wind  (nam, phía đất liền)   8 tầng + tầng mái  ~32 m
   Tầng 1 cao 6,0 m (tháp cao) / 5,0 m (tháp thấp); tầng điển hình 3,55 / 3,3 m.
   Số 25/21/12/10 tầng của bản cũ là số liệu quảng cáo 2017, không phải as-built.
7. Các tòa nhà nhỏ
   Shopvilla 3 tầng xây theo cặp (công bố 126 căn, lô 8,8 × 17,6 m). Mô hình
   truy được 68 khối đôi trên ảnh vệ tinh (136 căn theo dựng hình; vài khối có
   thể là khối đơn hoặc công trình phụ — ảnh không đủ rõ để tách). Mặt phố hướng
   theo trục lô đất: tầng trệt kính, tầng trên ban công kính; mặt hồi ốp ô vuông
   xám đậm dần lên trên như ảnh chụp. Ballroom mái lưới tối,
   khối dịch vụ, pavilion hình quạt cạnh Sand.
8. Tỉ lệ, vị trí, cảnh quan, nền đất, đường đi
   Mặt bằng đo trên ảnh vệ tinh (xem NGUỒN). Toàn bộ đường nhựa (có vạch sơn
   trích từ ảnh), lát gạch, cỏ, cát, hồ bơi, công viên nước, hồ phía tây đều là
   đa giác truy từ ảnh, có cao độ riêng (đường 0,08 m, lát 0,20 m, cỏ 0,24 m)
   nên bó vỉa thể hiện rõ. Quảng trường Arena: sân ô cờ tỏa tròn 640 ô, khán đài
   8 bậc có lối vào từ đại lộ, sân khấu nhạc nước, tượng thép Ali & Nino.
   ~3.340 cây/bụi theo vị trí tán cây phát hiện trên ảnh (dừa 3 loại, cau, cây
   tán rộng, bụi cảnh, cây bụi đụn cát).
9. Không có texture
   Vật liệu PBR từ ảnh scan CC0 (Poly Haven): vữa sơn, tường be, đường nhựa,
   gạch lát bê tông, đá granite, gạch hồ bơi, sàn gỗ, bê tông mái, cỏ, cát.
   Nguồn và tác giả: source/textures/licenses.json. Mọi mesh có UV box theo mét.

NGUỒN VÀ ĐỘ CHÍNH XÁC
Mặt bằng: ảnh vệ tinh Esri World Imagery zoom 18 (gần thẳng đứng, dùng cho
footprint) và Bing Aerial zoom 19 (chi tiết), quy về cùng lưới; 0,292 m/pixel;
gốc tọa độ = tâm quảng trường Arena; +X đông, +Y bắc thật. Ảnh vệ tinh KHÔNG
lưu trong repo; tools/v2_trace/fetch_imagery.py tải lại khi cần.
Số tầng/số phòng 4 tòa:
  https://kyluc.vn/tin-tuc/ky-luc/the-arena-cam-ranh-to-hop-nghi-duong-va-giai-tri-voi-3-530-phong-luu-tru-don-nhan-ky-luc-viet-nam
Chiều cao Light/Sea: https://en.wikipedia.org/wiki/List_of_tallest_buildings_in_Kh%C3%A1nh_H%C3%B2a_province
Shopvilla 126 căn, 3 tầng, lô 8,8 m: https://vneconomy.vn/cam-ranh-se-co-pho-mua-sam-soi-dong-bac-nhat.htm
  https://www.sggp.org.vn/shopvillas-ven-bien-xu-huong-dau-tu-moi-len-ngoi-post510677.html
Arena Square, khán đài, sân khấu nhạc nước:
  https://e.theleader.vn/the-largest-condotel-complex-project-arena-launches-4500-hotel-apartments-along-cam-ranh-peninsula-d2679.html
Tượng Ali & Nino 8,5 m: https://www.sggp.org.vn/buc-tuong-tinh-nhan-noi-tieng-the-gioi-xuat-hien-tai-viet-nam-post535572.html
Ảnh chụp chính thức trong references/ dùng để đối chiếu mặt đứng.
Vẫn là bản tái dựng theo ảnh, không phải CAD đo đạc: chiều cao tầng điển hình,
chiều sâu ban công, chi tiết mái, kiểu cây là ước lượng. Sai số mặt bằng ước
khoảng 1–3 m (độ phân giải ảnh + độ nghiêng ảnh vệ tinh).

DỰNG LẠI (chạy các lệnh từ thư mục art/hotels/EmpyreanCamRanh/)
Mã nguồn: source/v2/ (site_data.py = số đo; towers.py, villas.py, ground.py,
planting.py, props.py, cameras.py; build.py điều phối; qa.py kiểm tra lưới).
  blender -b --factory-startup -P source/v2/build.py
  blender -b source/Empyrean_CamRanh_Exterior_v2.blend -P source/v2/export_glb.py -- exports/Empyrean_Exterior_v2_Core.glb
  blender -b source/Empyrean_CamRanh_Exterior_v2.blend -P source/v2/render_cameras.py -- renders/v2 01_Aerial_from_land 2400 160
build.py tự tìm texture và file đầu ra theo vị trí của nó, không cần sửa ROOT.
Đa giác mặt đất đã tính sẵn trong source/v2/data/site_vectors.json. Muốn truy lại
từ ảnh (cần Python với pillow, numpy, opencv-python):
  python tools/v2_trace/fetch_imagery.py WORKDIR
  python tools/v2_trace/landcover.py WORKDIR
  python tools/v2_trace/site_vectors.py WORKDIR source/v2/data/site_vectors.json
Kết quả có thể lệch nhẹ so với bản đã commit do nén JPEG/nội suy khi ghép ảnh.

CHƯA LÀM TRONG V2
Video drone 20 s và FBX drone (exports/Empyrean_CamRanh_Exterior_Drone.fbx,
renders/Empyrean_CamRanh_Drone_20s.mp4) vẫn là bản dựng cũ.
Không có nội thất, collider hay LOD cho game.
