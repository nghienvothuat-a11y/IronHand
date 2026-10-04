from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

OUT = Path('/Users/mrk/IronHand/docs')
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path('/Users/mrk/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')
for n, f in [('Noto','NotoSans-Regular.ttf'),('NotoBold','NotoSans-Bold.ttf'),('NotoItalic','NotoSans-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(n, str(FONT/f)))
pdfmetrics.registerFontFamily('Noto',normal='Noto',bold='NotoBold',italic='NotoItalic',boldItalic='NotoBold')

NAVY=colors.HexColor('#102B40'); TEAL=colors.HexColor('#087F8C'); INK=colors.HexColor('#183447')
MUTED=colors.HexColor('#556C7A'); PALE=colors.HexColor('#EDF5F7'); LINE=colors.HexColor('#D4E2E8')
ORANGE=colors.HexColor('#B65E21'); CREAM=colors.HexColor('#FFF3E8')
W,H=A4; M=42; CW=W-2*M
styles={
 'body':ParagraphStyle('body',fontName='Noto',fontSize=9.6,leading=14.2,textColor=INK,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='Noto',fontSize=8.2,leading=11.5,textColor=MUTED,spaceAfter=5),
 'cell':ParagraphStyle('cell',fontName='Noto',fontSize=8.5,leading=12,textColor=INK),
 'headcell':ParagraphStyle('headcell',fontName='NotoBold',fontSize=8.4,leading=12,textColor=colors.white),
 'h2':ParagraphStyle('h2',fontName='NotoBold',fontSize=12.2,leading=16.7,textColor=TEAL,spaceAfter=6),
 'lead':ParagraphStyle('lead',fontName='NotoBold',fontSize=12,leading=18,textColor=NAVY,spaceAfter=12),
}

pdf=canvas.Canvas(str(OUT/'IronHand-Prototype-Plan-vi.pdf'),pagesize=A4)
pdf.setTitle('IronHand - Kế hoạch prototype mobile AR')
pdf.setAuthor('Codex | IronHand')
pdf.setSubject('Kế hoạch kỹ thuật và triển khai iOS trước, iPhone 13 Pro Max, 04/10/2026')
y=0; page=0

def p(text, style='body', width=None, x=None, gap=7):
    global y
    q=Paragraph(text,styles[style]); aw=width or CW
    _,h=q.wrap(aw,1000)
    if y-h<51: raise RuntimeError(f'Overflow page {page}: {text[:70]} y={y} h={h}')
    q.drawOn(pdf,M if x is None else x,y-h); y-=h+gap

def h(text):
    global y
    y-=4;p(text,'h2',gap=6)

def note(title,text,warm=False):
    global y
    q=Paragraph(f'<b>{title}</b><br/>{text}',styles['body']); _,hh=q.wrap(CW-24,1000)
    height=hh+20
    if y-height<51: raise RuntimeError(f'Note overflow {page}')
    pdf.setFillColor(CREAM if warm else PALE);pdf.roundRect(M,y-height,CW,height,7,fill=1,stroke=0)
    pdf.setFillColor(ORANGE if warm else TEAL);pdf.rect(M,y-height+7,3,height-14,fill=1,stroke=0)
    q.drawOn(pdf,M+12,y-10-hh);y-=height+12

def table(headers,rows,ratios):
    global y
    data=[[Paragraph(t,styles['headcell']) for t in headers]]
    data += [[Paragraph(str(t),styles['cell']) for t in row] for row in rows]
    t=Table(data,colWidths=[CW*r for r in ratios],hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LINEBELOW',(0,-1),(-1,-1),0.5,LINE),
    ]))
    _,hh=t.wrap(CW,1000)
    if y-hh<51: raise RuntimeError(f'Table overflow {page}: {hh} at {y}')
    t.drawOn(pdf,M,y-hh);y-=hh+13

def start(num,title,subtitle):
    global y,page
    if page: pdf.showPage()
    page=num
    pdf.setFillColor(NAVY);pdf.rect(0,H-14,W,14,fill=1,stroke=0)
    pdf.setFont('NotoBold',8.2);pdf.setFillColor(TEAL);pdf.drawString(M,H-39,'IRONHAND / PROTOTYPE PLAN')
    pdf.setFont('Noto',8.2);pdf.setFillColor(MUTED);pdf.drawRightString(W-M,H-39,'04/10/2026')
    pdf.setFont('NotoBold',23);pdf.setFillColor(NAVY);pdf.drawString(M,H-76,title)
    y=H-95;p(subtitle,'small',gap=14)
    pdf.setStrokeColor(LINE);pdf.line(M,38,W-M,38)
    pdf.setFont('Noto',7.5);pdf.setFillColor(MUTED);pdf.drawString(M,24,'iPhone 13 Pro Max trước | Android sau | Kế hoạch v1.0')
    pdf.setFont('NotoBold',8);pdf.drawRightString(W-M,24,f'{num:02d} / 10')

start(1,'Biến bàn tay thành vũ khí AR','Mục tiêu, phạm vi và các quyết định đã chốt')
p('Một game AR trên điện thoại: giáp 3D bám theo bàn tay thật, xoè tay để bắn, tiêu diệt quái trong căn phòng và dùng vàng để nâng cấp.','lead')
p('Thiết bị nghiệm thu đầu tiên là <b>iPhone 13 Pro Max</b>. Phát triển iOS trước, dùng camera sau; một tay cầm điện thoại, tay còn lại xuất hiện trước camera. Thử cả tay trái và tay phải, ưu tiên bố cục ngang như minh hoạ. Android chỉ triển khai sau khi trải nghiệm iOS vượt các cổng kiểm thử.')
table(['Từ minh hoạ','Cách đưa vào prototype'],[
 ('4.jpg - ý tưởng Iron Hand','Giáp cơ khí nguyên bản, lõi năng lượng, HUD xanh cyan. Giữ cảm giác công nghệ; không sao chép trực tiếp mẫu nhân vật thương mại.'),
 ('5.jpg - quét và thay tay','Quét là calibration vị trí/kích thước tay + hiệu ứng lắp giáp. Không phải quét 3D tạo chính xác cả cánh tay.'),
 ('6.jpg - giao chiến','Quái nằm trong không gian căn phòng; đạn/VFX đi từ giáp tới mục tiêu. HUD HP/mana; tâm ngắm do camera điều khiển.'),
 ('7.jpg - nhiều giáp','ALP-2, CI-1, DEL-10 gợi ý ba tier dùng chung skeleton, mở level 1/3/5. Dùng vàng theo yêu cầu; không lấy giá gem/stats trong ảnh làm balance.'),
 ('8.jpg - ManoMotion','ManoMotion là ứng viên SDK cần kiểm thử trên thiết bị và phiên bản Unity hiện tại; ảnh cũ không chứng minh tương thích hôm nay.')
],[.30,.70])
h('Bản chơi được cần chứng minh điều gì?')
p('<b>1.</b> Giáp và ngón tay phản ứng đủ nhanh để người chơi cảm thấy đang mặc giáp. <b>2.</b> Xoè tay bắn dễ hiểu và không bắn nhầm. <b>3.</b> Quái giữ đúng vị trí trong phòng khi xoay máy. <b>4.</b> Chơi 3-5 phút thấy vui, đủ thoải mái và muốn nâng cấp.')
note('Định nghĩa hoàn thành','Một build cài được trên iPhone 13 Pro Max: calibration, 3 giáp, 3 loại quái, 5 wave, máu/mana, vàng/XP, nâng cấp và lưu tiến độ. Có log đo thực tế, video demo và báo cáo giới hạn.')
p('Ngoài phạm vi v1: multiplayer, backend, tài khoản, GPS, map ngoài trời, quét phòng đầy đủ, xoá da hoàn hảo, theo dõi khuỷu tay, App Store launch, quảng cáo và IAP. Đây là kế hoạch; các chỉ số phía sau là mục tiêu đề xuất, chưa phải kết quả benchmark.','small')

start(2,'Chọn nền tảng và SDK','Quyết định công nghệ có điều kiện, khóa phiên bản sau tuần thử nghiệm')
table(['Lớp','Lựa chọn và cách khóa'],[
 ('Engine / render','Unity 6.3 LTS là ứng viên đầu tiên, URP cấu hình mobile, Metal trên iOS. Chốt patch sau khi mẫu AR + hand SDK build thành công. [1]'),
 ('AR thế giới','AR Foundation 6.x và ARKit XR Plug-in cùng bộ phiên bản tương thích. XR Origin, AR Camera, plane, raycast và anchor. Android dùng ARCore XR Plug-in ở giai đoạn sau. [2]'),
 ('Theo dõi tay ưu tiên','ManoMotion 2.1.2: kiểm tra sample iOS, dữ liệu khớp/ngón, callback, độ trễ, AR Foundation input và license. Listing tham chiếu Unity 6000.0.67; không suy ra đã hỗ trợ 6.3. [3]'),
 ('Phương án dự phòng','MediaPipe Hand Landmarker native iOS qua Swift/Objective-C + C bridge tới Unity. Nhận frame của phiên AR hiện có; tránh khởi chạy camera riêng. [4]'),
 ('Model / rig','Tripo tạo mesh từ text/ảnh/multiview; Blender làm sạch, rig và weights; xuất FBX sang Unity. Assistant thực hiện cả pipeline, không giả định thuê artist. [5]'),
 ('Dữ liệu gameplay','C# + ScriptableObject cho cấu hình; JSON local có schemaVersion, ghi file tạm rồi thay thế, backup và kiểm tra dữ liệu.')
],[.25,.75])
note('Không nhầm ARKit, XR Hands và camera RGB','AR Foundation lo môi trường và pose camera. XR Hands là giao diện nhận dữ liệu từ provider có hand tracking; cài package này không tự biến camera iPhone thành bộ theo dõi ngón tay. API HandTrackingProvider của visionOS không phải lối tắt cho game iPhone. [2][6]')
h('Quyết định sau 5 ngày')
p('Nếu ManoMotion chạy ổn với Unity 6.3 và chia sẻ frame đúng: khóa bộ đó. Nếu có lỗi phiên bản: thử nhánh Unity mà SDK công bố tương thích trong sandbox kỹ thuật. Nếu không đạt về pose, độ trễ, camera hoặc license: chuyển MediaPipe qua cùng IHandTrackingProvider, giữ nguyên gameplay.')
p('Chi phí tham chiếu cần xác nhận trước giao dịch: ManoMotion listing khoảng <b>US$50/seat</b> tại thời điểm nghiên cứu; chưa bao gồm mọi điều kiện phân phối hoặc dịch vụ. Tripo tính theo gói/credit đang có; không ấn định tổng tiền khi chưa biết gói và số lần thử. [3]','small')

start(3,'Bàn tay: từ pixel đến bộ giáp','Giảm độ trễ trước, sau đó mới tăng độ tinh xảo của mesh')
note('Một camera, hai nhiệm vụ','AR Session sở hữu camera sau. Frame gốc nuôi hand detector; camera background dùng để hiển thị AR. Không mở WebCamTexture hoặc một phiên camera khác đồng thời. Không đưa ảnh đã render giáp vào detector.')
table(['Bước','Cách triển khai'],[
 ('01. Thu nhận','ManoMotion có adapter AR Foundation dùng RenderTexture. MediaPipe có thể dùng XRCpuImage/native buffer. Giữ timestamp, pose/intrinsics tương ứng và vòng đời buffer. [7][11]'),
 ('02. Chuẩn hóa','Resize/crop, sửa orientation, handedness và mirror. Lưu phép biến đổi để chuyển landmarks về đúng pixel trên màn hình.'),
 ('03. Nhận dạng','Một tay hoạt động; xử lý bất đồng bộ, queue chỉ giữ frame mới nhất. Thử inference 15-30 Hz, render độc lập; đo rồi chọn.'),
 ('04. Ước lượng pose','Landmarks 2D căn vị trí/kích thước giáp; các khớp 3D tương đối ước lượng hướng lòng bàn tay và góc ngón. Lọc rung có xét độ trễ.'),
 ('05. Retarget','Ánh xạ dữ liệu detector vào skeleton chung. Dùng bind-pose offsets, giới hạn góc khớp và pose cuối đáng tin cậy để tránh ngón lật.'),
 ('06. Điều khiển','Gesture state machine đọc Open/Closed/Unknown; combat chỉ nhận fireIntent, validity và tuổi dữ liệu. Chuẩn hóa trạng thái hợp lệ theo SDK.')
],[.24,.76])
h('Calibration 3-5 giây')
p('Hướng dẫn đưa trọn bàn tay vào khung, giữ tay mở trong ánh sáng đủ tốt. Thu nhiều mẫu ổn định, lấy median kích thước bàn tay, lưu tay trái/phải và độ rộng rig. Hiệu ứng “scan 100%” chạy sau khi dữ liệu đạt ngưỡng; không đếm thời gian rồi báo thành công giả.')
p('MediaPipe có 21 landmarks; “world landmarks” dùng đơn vị mét nhưng gốc ở tâm bàn tay, <b>không phải AR world</b>. Muốn đặt tay 3D theo căn phòng phải thêm ước lượng pose/depth và calibration camera. V1 có thể ưu tiên overlay nhìn đúng trên ảnh hơn độ sâu tuyệt đối. [4]')
note('Giới hạn hình học cần chấp nhận','V1 dùng găng + cuff ngắn. Detector bàn tay không cung cấp khuỷu tay; hướng cẳng tay chỉ suy ra từ cổ tay. SDK mask/segmentation hỗ trợ phân lớp hình ảnh, không tái tạo nền để xoá da thật. Giáp hơi dày và glow nhẹ giúp che sai lệch nhỏ.',True)

start(4,'Ngắm bắn và không gian AR','Tay là cò bắn; camera là hướng ngắm trong phiên bản đầu')
h('Quy tắc ngắm có chủ ý')
p('Người chơi xoay điện thoại để đặt reticle lên quái. Khi tay mở ổn định khoảng 120 ms, vũ khí bắt đầu bắn theo cooldown; nắm tay, hết mana hoặc mất dữ liệu thì dừng. Dùng ngưỡng mở/đóng khác nhau và debounce để trạng thái không chớp liên tục.')
p('Lòng bàn tay hướng vào camera thì pháp tuyến thật thường hướng về phía người chơi. Vì vậy không dùng trực tiếp pháp tuyến đó để bắn quái phía trước. V1 raycast từ camera qua reticle; tia/đạn hình ảnh xuất phát ở muzzle của giáp và đi tới hit point. Hit gameplay dùng cùng mục tiêu; có aim assist nhỏ, cấu hình được.')
table(['Không gian','Hành vi'],[
 ('World Arena Anchor','Quái, spawn points, projectile thế giới và floor proxy nằm dưới arena anchor. Không parent quái vào camera. Khi máy xoay, quái vẫn ở vị trí căn phòng. [8]'),
 ('Camera / người chơi','Camera cung cấp tâm ngắm và vị trí mục tiêu của quái. Sát thương kích hoạt khi quái tới bán kính tấn công, theo cooldown; không cần collider vật lý va mặt.'),
 ('Hand renderer','Giáp chạy theo pose tay ước lượng; có thể dùng pass riêng để depth của tay thật không che mất chính giáp. HUD luôn đọc rõ.'),
 ('Map cục bộ','Cho người chơi xác nhận vùng trống phía trước, khoảng cách khởi đầu 1,5-3 m, giới hạn theo không gian thực tế. Không cần GPS hay cloud anchors.')
],[.28,.72])
h('Spawn và quái tiếp cận')
p('V1 bắt đầu bằng drone bay để chứng minh trận đấu mà chưa cần hiểu vật cản trong phòng. Sau đó thêm robot thường/nặng trên mặt phẳng sàn đã chọn; di chuyển trong arena đơn giản. Random vị trí có seed, giữ khoảng cách tối thiểu, không sinh sát camera. Sau spawn, vị trí thuộc world; không kéo quái theo góc nhìn.')
h('Tracking và che khuất')
p('Nếu hand pose quá cũ: dừng bắn trong tối đa 200 ms, fade giáp và nhắc đưa tay vào khung. Nếu AR world tracking không đáng tin: pause spawn, damage và timer; khôi phục tracking rồi đếm ngược tiếp tục. Nếu session reset, dựng lại arena rõ ràng, không âm thầm di chuyển quái.')
p('Plane detection không phải bản đồ vật cản đầy đủ. Environment depth/occlusion là bước tăng chất lượng sau MVP, bật theo capability và kết quả đo. Tay gần camera và nền ít chi tiết cần test; không mặc định có LiDAR là mọi ngón tay sẽ có depth chính xác. [9][10]','small')

start(5,'Vòng lặp chơi và cân bằng đầu','Tất cả số liệu trang này là cấu hình khởi điểm để playtest')
p('<b>Quét tay -&gt; chọn giáp -&gt; chơi 5 wave -&gt; nhận vàng/XP -&gt; nâng cấp -&gt; thử lại.</b> Một lượt dự kiến 3-5 phút. Giữa wave có khoảng nghỉ 5-8 giây để hạ tay; vàng nhặt tự động, không buộc chạm màn hình giữa chiến đấu.')
table(['Hệ thống','Cấu hình đầu tiên'],[
 ('Người chơi','HP 100; mana 100. Đạn cơ bản 10 damage, 4 mana, 3 phát/giây. Hồi 12 mana/giây chỉ khi không bắn; hết mana thì phải nghỉ.'),
 ('Giáp level 1 / 3 / 5','Scout miễn phí; Pulse giá 200 vàng khi đạt lv3; Aegis giá 500 vàng khi đạt lv5. Chung rig, khác mesh/VFX và modifier. Chưa cân bằng ưu thế tuyệt đối.'),
 ('XP / lưu level','Đạt lv2/3/4/5 ở tổng XP 100/250/450/700. Level mở quyền mua giáp; vàng mua hoặc nâng cấp, XP không bị tiêu.'),
 ('Nâng cấp bền vững','Damage +2/rank, HP tối đa +10/rank, mana tối đa +10/rank; mỗi nhánh tối đa 5 rank. Giá rank tiếp theo = round(50 × 1,5^rank hiện có).'),
 ('Nhịp wave','5 wave, mỗi wave 35 giây + tối đa 15 giây dọn quái còn lại. Spawn interval 4 -&gt; 2,5 giây; tối đa 5 quái sống. Qua wave tăng HP quái nhẹ, ưu tiên đọc được mục tiêu.')
],[.28,.72])
table(['Quái','HP / tấn công','Thưởng / vai trò'],[
 ('Drone','30 HP; 8 damage; cooldown 2 giây','10 vàng + 10 XP. Bay chậm, model đơn giản, dùng cho proof kỹ thuật.'),
 ('Robot thường','50 HP; 12 damage; cooldown 2 giây','15 vàng + 15 XP. Dùng sàn arena, rõ animation trước khi đánh.'),
 ('Robot nặng','100 HP; 20 damage; cooldown 2,5 giây','30 vàng + 30 XP. Chậm, lớn hơn, dùng chung skeleton robot thường.')
],[.24,.34,.42])
h('Quy tắc trận đấu')
p('Mỗi lần chết quái chỉ thưởng một lần. Thưởng được cộng ngay và lưu theo batch an toàn; thua vẫn giữ vàng/XP đã nhận. Thắng wave 5 có bonus dự kiến 50 vàng/50 XP. HP và mana hiện tại reset mỗi lượt; nâng cấp và giáp đã mua tồn tại sau khi đóng app.')
p('Không dùng số liệu này như dự báo retention hay doanh thu. Playtest cần đo time-to-kill, tỉ lệ bắn trúng, thời gian cạn mana, số lượt tới lv3 và mỏi tay; điều chỉnh economy bằng dữ liệu đó.','small')

start(6,'Tự tạo model: Tripo + Blender','Assistant phụ trách mesh, rig, tối ưu và kiểm tra import Unity')
table(['Công đoạn','Sản phẩm và kiểm tra'],[
 ('1. Thiết kế','Tạo thiết kế cơ khí riêng: năm ngón tách rõ, giáp chia đốt, palm core, cuff ngắn. Giữ cùng silhouette và tỉ lệ cho ba tier.'),
 ('2. Tripo','Text/ảnh hoặc multiview -&gt; chọn mesh sạch nhất -&gt; export khi gói cho phép. Lưu prompt, nguồn, task ID và file gốc. Auto-rig vẫn phải kiểm tra ngón tay. [5]'),
 ('3. Blender cleanup','Kiểm tra đủ 5 ngón, tách ngón dính, sửa normals, lỗ mesh, intersections; giảm poly, bake texture và apply scale. Lưu bản .blend chỉnh được.'),
 ('4. Skeleton chung','Tạo wrist/palm và chuỗi khớp cho 5 ngón; local axes/bind pose nhất quán. Giáp cứng có thể parent từng mảnh theo xương, vùng mềm mới dùng skin weights.'),
 ('5. Rig và retarget','Thiết lập Open, Fist, Pinch và back-of-hand test poses. Kiểm tra biến dạng cổ tay, ngón cái, duỗi/gập cực hạn. Map landmarks qua adapter, không gắn cứng với một SDK.'),
 ('6. Unity','Xuất FBX; rig bàn tay dùng Generic/custom. Gắn material URP, palm muzzle, collider tối giản. So ảnh render với mesh nguồn, kiểm tra scale/mirror và chuyển tier.')
],[.25,.75])
table(['Ngân sách thử nghiệm','Mục tiêu ban đầu'],[
 ('Giáp bàn tay','10.000-20.000 triangles; texture 1K-2K; 1-2 materials; một skeleton chung cho 3 biến thể.'),
 ('Quái','3.000-8.000 triangles/con; texture 1K; 1-2 materials. Robot nặng tái dùng skeleton/animation robot thường.'),
 ('VFX / cảnh','Object pool; giới hạn hạt và transparency; tránh nhiều realtime lights/shadow. Tăng chất lượng sau khi chạy bền 10 phút.')
],[.36,.64])
note('Nếu mesh AI không đạt','Assistant làm bộ giáp low-poly dạng mảnh cơ khí trực tiếp trong Blender để giữ tiến độ, rồi thay hình thức khi có mesh tốt. Tripo khuyên chạy rig-check; các rig type công bố không có bàn tay rời, nên không giả định auto-rig ngón tay sẽ đạt. [12]',True)
p('Tripo công bố export FBX/GLB; chất lượng phải kiểm tra từng asset. Quyền export là phụ thuộc thực tế: tài khoản Free hiện hiển thị cần nâng cấp để xuất 3D. Chưa mua gói. Tài liệu không coi preview mới là asset đã rig và chạy trong game. [13]','small')

start(7,'Kiến trúc triển khai và UX','Tách phần dễ thay đổi để có thể đổi SDK mà không viết lại trò chơi')
table(['Module / giao diện','Trách nhiệm'],[
 ('ARSessionController','Camera permission, tracking state, plane scan, anchor, session reset, capability và pause toàn trận.'),
 ('IFrameSource','Frame gốc + timestamp + orientation/crop + intrinsics/pose; quản lý buffer và vòng đời camera.'),
 ('IHandTrackingProvider','ManoMotion hoặc MediaPipe -&gt; HandFrame gồm handedness, joints/landmarks, validity và thời gian capture/result.'),
 ('HandPoseSolver / RigDriver','Calibration, scale, pose, filtering, joint mapping, hide/fade khi mất tay và áp rig.'),
 ('GestureController / Weapon','State Open/Closed/Unknown; debounce; cooldown, mana, aim ray, hit damage và VFX.'),
 ('Arena / Spawn / Enemy','Spawn có seed, giới hạn quái, object pooling, state machine Approach/Attack/Hit/Dead, target là pose camera.'),
 ('Progression / SaveService','Vàng, XP, inventory, upgrade; ScriptableObject định nghĩa item, JSON lưu trạng thái với schemaVersion và backup.'),
 ('HUD / Diagnostics','HP, mana, wave, reticle, thông báo tracking, FPS/frame time, pose age, mất tay, build/device/SDK versions.')
],[.40,.60])
h('Các màn hình cần làm')
p('<b>Boot</b>: kiểm tra camera và hỗ trợ AR. <b>Calibration</b>: hướng dẫn giữ máy, chọn vùng trống, nhận tay và lắp giáp. <b>Combat</b>: HUD ít chữ, tâm ngắm rõ, pause lớn. <b>Result/Workshop</b>: phần thưởng, giáp bị khoá theo level, nút nâng cấp có giá và chỉ số trước/sau.')
h('Lưu dữ liệu và tính nhất quán')
p('Không serialize GameObject. Save gồm schemaVersion, XP, gold, owned/equipped hand IDs và upgrade ranks. Ghi temp -&gt; validate -&gt; thay file chính, giữ backup gần nhất; migrate hoặc recover khi file hỏng. Test kill trùng callback, reload app giữa result, không đủ vàng và upgrade chạm cap.')
p('Trong prototype xử lý ảnh trên máy, không cần backend hoặc tải video camera lên server. Diagnostics mặc định chỉ lưu số liệu; nếu cần video để debug thì dùng phiên ghi có chủ ý. Simulator/Editor hữu ích cho gameplay, nhưng không thay nghiệm thu tracking bằng điện thoại thật.','small')

start(8,'Kiểm thử và cổng nghiệm thu','Mục tiêu đo trên iPhone 13 Pro Max; chưa có benchmark thực tế')
table(['Gate','Cách đo','Điều kiện đề xuất'],[
 ('A. AR + camera','Khối gắn anchor; xoay máy, di chuyển nhẹ, tay che một phần ảnh.','Vật thể không đi theo camera; mất tracking có feedback và phục hồi có kiểm soát.'),
 ('B. Giáp bám tay','Overlay landmark/rig, ghi hình tay trái/phải, xoè/nắm, lòng/mu tay.','Trong vùng sử dụng công bố: sai số reprojection median <5%, p95 <10% bề rộng lòng bàn tay.'),
 ('C. Độ trễ','Video tốc độ cao tay thật + màn hình; log capture/inference/render.','Motion-to-overlay median <100 ms, p95 <150 ms. Không chỉ báo inference time.'),
 ('D. Gesture','100 lần mở/đóng + các chuyển động không định bắn.','Nhận đúng &gt;=95/100; &lt;=1 bắn nhầm/phút. Mất pose -&gt; dừng bắn &lt;=200 ms.'),
 ('E. Chạy bền','10 phút, AR + tay + tối đa 5 quái; đo theo đoạn thời gian.','Mục tiêu 30 FPS bền; ngân sách trung bình ~33 ms/frame, p95 <40 ms. Ghi nhiệt và giảm xung.'),
 ('F. Gameplay / save','Một lượt 5 wave; chết, restart, app background, kill process, load save.','Không thưởng trùng; gold/XP/giáp đúng sau restart; pause tracking không gây damage oan.'),
 ('G. Cảm giác chơi','3-5 người thử nếu có; phiên 3-5 phút, tay thuận khác nhau.','Hiểu mở tay để bắn, ngắm dễ, dùng pause dễ; ghi thời điểm mỏi tay và lỗi khó chịu nhất.')
],[.20,.40,.40])
h('Ma trận môi trường tối thiểu')
p('Ánh sáng trong nhà đủ sáng/thiếu sáng/ngược sáng; nền có chi tiết/tường trơn; nhiều màu da; tay nhỏ/lớn; kính/đồng hồ nếu có; tay ở giữa/mép khung; khoảng cách thử 25-70 cm; cử động chậm/nhanh; tư thế cầm ngang trái/phải. Khoảng thử không phải cam kết mọi trường hợp đều hỗ trợ.')
note('Thứ tự giảm tải nếu không đạt FPS','Đo CPU/GPU/inference trước. Hạ tần suất hoặc độ phân giải detector; giảm copy buffer; giảm transparency/VFX; hạ texture/shadow; giới hạn quái. Không che lỗi bằng cách chỉ báo FPS trung bình hoặc thử rất ngắn.',True)
p('Gate B-D quyết định có tiếp tục sản xuất đủ content hay phải đổi SDK/tương tác. Lưu file đo, cấu hình build, phiên bản OS/SDK và video test để kết quả có thể lặp lại. Những ngưỡng này là acceptance targets do dự án đề xuất, không phải số liệu bảo đảm của vendor.','small')

start(9,'Lộ trình, khối lượng và vai trò','Ước lượng công việc có điều kiện; không phải lời hứa thời gian chạy của AI')
table(['Giai đoạn','Việc chính / đầu ra','Ước lượng'],[
 ('Tuần thử 1','Ngày 1: AR anchor. Ngày 2: SDK landmarks + frame. Ngày 3: rig đơn giản. Ngày 4: mở tay/aim/bắn. Ngày 5: 10 phút trên máy và quyết định SDK.','5 ngày dev'),
 ('Tracking / rig','Sửa calibration, mapping, filter, render, pose stale và pause. Khóa provider interface.','5-7 ngày dev'),
 ('Combat slice','Drone, damage, mana, waves, pooling, robot và HUD; một lượt đầy đủ.','7-9 ngày dev'),
 ('Progression / UX','3 giáp, XP/level, workshop, save/recover, tutorial, sound/haptic.','5-7 ngày dev'),
 ('Tối ưu / nghiệm thu','Device profiling, sửa edge cases, test dài, balancing, build demo và ghi hạn chế.','8-12 ngày dev')
],[.23,.57,.20])
p('<b>Tổng dev: khoảng 30-40 ngày công</b>, tương đương 6-8 tuần nếu có thể phân chia công việc. Asset/rig khoảng <b>8-15 ngày công</b> riêng; nếu cùng một người phải làm mọi phần nối tiếp, nên dự trù khoảng <b>8-11 tuần</b>. Native MediaPipe fallback có thể thêm 1-3 tuần. Android dự trù thêm 1-2 tuần sau gate iOS, tùy thiết bị và lỗi tích hợp.')
table(['Assistant thực hiện','Người dùng hỗ trợ'],[
 ('Nghiên cứu, tạo project/code, adapter SDK, gameplay, save, HUD, cấu hình build.','Cung cấp quyền truy cập tài khoản/license cần thiết, Apple signing/team và kết nối iPhone thực tế.'),
 ('Tạo concept/mesh qua Tripo; Blender cleanup, skeleton, rig, texture và Unity import.','Thử cảm giác cầm máy, xoè/nắm, ngắm bắn; phản hồi mỏi tay, độ trễ và hình thức giáp.'),
 ('Tạo test scenes, log, phân tích profiler và sửa lỗi; chuẩn bị build/demo.','Chấp thuận chi tiêu cụ thể khi công cụ có giao dịch phát sinh; cung cấp thêm Android ở giai đoạn sau.')
],[.56,.44])
note('Chi phí và phụ thuộc cần giữ hữu hình','SDK ManoMotion và credit Tripo phụ thuộc license/gói. Không cần backend trả phí cho MVP. Trước khi khóa lịch: cần build ký được lên iPhone, SDK nhập frame AR đúng và một mesh ngón tay rig được. Không xem video quảng cáo hoặc asset “game-ready” là thay thế cho ba kiểm tra này.')
p('Đầu ra bàn giao: source Unity và package lock, source Blender/mesh gốc, cấu hình economy, build iOS, log test, video demo và danh sách lỗi còn lại. Chỉ mở rộng Android sau khi chứng minh phần điều khiển chính trên iPhone.','small')

start(10,'Nguồn và quyết định còn mở','Nguồn primary tra cứu ngày 04/10/2026; liên kết có thể bấm trong PDF')
refs=[
 ('[1] Unity 6 release support','https://unity.com/releases/unity-6/support','Unity 6.3 LTS và chính sách hỗ trợ.'),
 ('[2] AR Foundation 6.2 - overview','https://docs.unity3d.com/Packages/com.unity.xr.arfoundation@6.2/manual/index.html','Provider iOS/Android, camera, planes, anchors và bảng tính năng.'),
 ('[3] ManoMotion SDK - Unity Asset Store','https://assetstore.unity.com/packages/tools/game-toolkits/manomotion-sdk-hand-tracking-for-smartphones-compatible-with-ope-280702','2.1.2, release 18/02/2026, Unity 6000.0.67, US$50/seat trước thuế.'),
 ('[4] MediaPipe Hand Landmarker - iOS','https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/ios','Native iOS, dữ liệu landmarks và chế độ xử lý frame.'),
 ('[5] Tripo Developers - Introduction','https://developers.tripo3d.ai/en/docs/introduction','Generation từ text/ảnh/multiview và các bước xử lý model.'),
 ('[6] Unity XR Hands 1.6','https://docs.unity3d.com/Packages/com.unity.xr.hands@1.6/manual/index.html','XR Hands cần provider triển khai; không phải detector camera RGB.'),
 ('[7] AR Foundation - Image capture','https://docs.unity3d.com/Packages/com.unity.xr.arfoundation@6.2/manual/features/camera/image-capture.html','XRCpuImage, CPU/GPU, chuyển đổi và dispose tài nguyên.'),
 ('[8] ARCore - Working with Anchors','https://developers.google.com/ar/develop/anchors','Nguyên tắc world anchor, dùng chung anchor và cập nhật pose.'),
 ('[9] Apple - Understanding World Tracking','https://developer.apple.com/documentation/arkit/understanding-world-tracking','Ảnh có chi tiết, ánh sáng, motion blur và trạng thái tracking.'),
 ('[10] ARCore - Depth adds realism','https://developers.google.com/ar/develop/depth','Depth-from-motion, phụ thuộc thiết bị và khoảng chính xác tốt nhất.'),
 ('[11] ManoMotion - InputManagerARFoundation','https://sdk.manomotion.com/SDK_Pro_v2.0/class_mano_motion_1_1_camera_system_1_1_input_manager_a_r_foundation.html','Adapter lấy ảnh ARCameraBackground qua RenderTexture; tài liệu SDK 2.0.'),
 ('[12] Tripo Developers - Auto Rig','https://developers.tripo3d.ai/en/docs/animations-rig','Rig-check, rig types được công bố và định dạng rig xuất.'),
 ('[13] Tripo Developers - Convert Format','https://developers.tripo3d.ai/en/docs/models-convert','Định dạng xuất và cấu hình workflow chuyển đổi.'),
]
for label,url,desc in refs:
    p(f'<link href="{url}" color="#087F8C"><b>{label}</b></link><br/>{desc}','small',gap=9)
h('Cần chốt bằng prototype, không bằng suy đoán')
p('SDK thực sự chạy tốt nhất; patch Unity/AR packages được khóa; vùng khoảng cách tay thoải mái; có cần mask/occlusion; chất lượng mesh Tripo sau rig; độ bền FPS/latency; lịch sản xuất sau tuần thử. Tất cả đều có tiêu chí đo ở trang 8.')
p('Giá, release SDK và khả năng theo gói có thể thay đổi. Kế hoạch phân biệt facts từ nguồn với lựa chọn kỹ thuật của dự án; mọi performance target, budget poly, timeline và con số gameplay đều do dự án đề xuất. Bản PDF chưa xác nhận bất kỳ build, model hay benchmark mới nào đã hoàn tất.','small')
pdf.save()
print(OUT/'IronHand-Prototype-Plan-vi.pdf')
