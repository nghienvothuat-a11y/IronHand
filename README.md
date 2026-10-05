# IronHand

Prototype game AR trên di động: gắn tay giáp 3D lên bàn tay qua camera, dùng cử chỉ để bắn quái vật và nhận vàng nâng cấp. Ưu tiên iPhone 13 Pro Max, sau đó Android.

## Trạng thái hiện tại

- Có kế hoạch kỹ thuật, model gốc xuất từ Tripo, model Blender đã rig và animation thử cử chỉ.
- Có FBX/GLB, texture, quy ước xương và script kiểm tra rig.
- Có project Unity 6.3 LTS trong `Unity/`, bản mô phỏng Mac và pipeline build iOS.
- Bản test hiện tại: quái đứng yên, không phản công; rocket bay tới mục tiêu rồi mới trừ máu, nổ và tung mảnh vỡ khi chết. Giữ 5 wave, vàng/XP, giáp, workshop và save local.
- Provider iOS dùng Apple Vision nhận 21 khớp 2D. Giáp được fit theo khớp và thêm lớp kim loại che các khe, có nút chỉnh độ phủ. Đây chưa phải segmentation da hoặc pose tay 3D đã nghiệm thu.
- Camera, sàn AR, calibration và chiến đấu đã chạy trên iPad thế hệ 8. Người dùng đã xác nhận độ phủ tay ổn, rocket và hiệu ứng nổ hoạt động; chưa nghiệm thu mọi góc xoay/chuyển động hoặc độ ổn định nhiệt dài hạn.
- Kết quả chạy thiết bị và các giới hạn được ghi trong `docs/Prototype-Runbook.txt`.

## Nội dung repo

| Thư mục | Nội dung |
| --- | --- |
| `docs/` | Kế hoạch prototype bằng tiếng Việt, script tạo PDF và thông tin asset Tripo |
| `art/blender/` | File Blender, hướng dẫn chỉnh rig và báo cáo kiểm tra |
| `art/previews/` | Ảnh model và các tư thế thử |
| `assets/source/` | FBX gốc từ Tripo |
| `assets/exports/` | FBX/GLB đã rig, texture và quy ước xương |
| `Unity/` | Project Unity, scene, C#, bridge Apple Vision, cấu hình ARKit/URP và tests |
| `tools/` | Script dựng model, kiểm tra rig và build/cài app |
| `tools/mcp-setup/` | Ghi chú kết nối Blender/Tripo MCP và script kiểm tra chỉ đọc |

## Xem và dựng lại model

Mở `art/blender/IronHand_MK1_Rigged.blend` bằng Blender 5.2. Nhấn Space trong viewport để xem animation thử. Chi tiết điều khiển và giới hạn của model nằm trong `art/blender/README.txt`.

Các script hiện dùng đường dẫn `/Users/mrk/IronHand`; cần chỉnh đường dẫn nếu clone vào vị trí khác. Script tạo PDF còn dùng đường dẫn font Noto cục bộ và thư viện ReportLab.

```sh
blender --background --python tools/build_hand_rig.py
blender --background --python tools/validate_hand_rig.py
```

Script dựng lại sẽ ghi đè các đầu ra model; lưu riêng các chỉnh sửa thủ công trước khi chạy. Cần có lệnh `blender` trong PATH hoặc dùng đường dẫn đầy đủ tới Blender.

## MCP

Xem `tools/mcp-setup/README.txt` để biết cấu hình đã kiểm tra trên máy phát triển. Các server và thông tin xác thực được cài ngoài repo. API key, log, bộ cài tải về và file tạm không được đưa vào Git. Credit Tripo API tách riêng với gói Tripo Studio.

Model là bản thử cơ khí, còn cần chỉnh khe giáp, xuyên mesh và hiệu chỉnh khớp khi nối với hand tracking thực tế. Ghi chú chặn export trong PDF kế hoạch là trạng thái cũ; model đã xuất và rig thành công sau đó.

## Chạy prototype

Mở `Unity/` bằng Unity **6000.3.19f1**, mở scene `Assets/Scenes/IronHand.unity` và Play. Editor/Mac chạy chế độ mô phỏng; chỉ iOS dùng camera/AR thực.

```sh
bash tools/build_unity.sh prepare
bash tools/build_unity.sh test
bash tools/build_unity.sh mac
bash tools/build_unity.sh ios
```

`prepare` tạo lại scene và cấu hình mặc định; lưu các chỉnh sửa scene thủ công trước khi chạy. Build iOS cần Unity iOS Build Support và Xcode. Ký/cài app dùng `tools/install_iphone.sh` với `IRONHAND_APPLE_TEAM` và `IRONHAND_DEVICE` của máy người phát triển. Không lưu thông tin xác thực hoặc provisioning profiles trong repo.

Trên Mac: Enter để tiếp tục setup, giữ Space để bắn, giữ chuột phải rồi kéo để ngắm; H thử mất tay, T thử mất AR, L đổi tay, Esc tạm dừng. Save mô phỏng tách riêng save iPhone.
