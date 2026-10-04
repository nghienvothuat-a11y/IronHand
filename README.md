# IronHand

Prototype game AR trên di động: gắn tay giáp 3D lên bàn tay qua camera, dùng cử chỉ để bắn quái vật và nhận vàng nâng cấp. Ưu tiên iPhone 13 Pro Max, sau đó Android.

## Trạng thái hiện tại

- Có kế hoạch kỹ thuật, model gốc xuất từ Tripo, model Blender đã rig và animation thử cử chỉ.
- Có FBX/GLB, texture, quy ước xương và script kiểm tra rig.
- Đã kiểm tra rig trong Blender và kiểm tra nhập lại FBX; **chưa có ứng dụng Unity/iOS chạy được**, hand tracking thời gian thực hoặc gameplay.

## Nội dung repo

| Thư mục | Nội dung |
| --- | --- |
| `docs/` | Kế hoạch prototype bằng tiếng Việt, script tạo PDF và thông tin asset Tripo |
| `art/blender/` | File Blender, hướng dẫn chỉnh rig và báo cáo kiểm tra |
| `art/previews/` | Ảnh model và các tư thế thử |
| `assets/source/` | FBX gốc từ Tripo |
| `assets/exports/` | FBX/GLB đã rig, texture và quy ước xương |
| `tools/` | Script dựng, xem và kiểm tra model bằng Blender |
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
