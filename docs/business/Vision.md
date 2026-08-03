# Vision: Personal IELTS Learning Dashboard (Bảng điều khiển học IELTS cá nhân)

## Status
Draft (revision 4 — IELTS Academic adaptive plan, target 6.5 in 24 weeks, 60 minutes/day, multi-user)

## Revision 4 Product Direction
- The product serves individual IELTS Academic learners with separate accounts and fully
  isolated learning histories.
- The initial target profile is a software engineer starting near band 3.5, aiming for overall
  6.5 with no skill below 6.0 in 24 weeks, studying 60 minutes per day.
- The product outcome is no longer "four exercises every day." It is one coherent daily
  session: 10 minutes of vocabulary/mistake review plus 50 minutes allocated across the
  highest-value primary and supporting skills.
- Difficulty progresses through six four-week phases and is recalibrated from assessed
  performance rather than inferred from elapsed time alone.
- Registration, login, account ownership, and per-user data isolation are product-level
  requirements because multiple learners may use the hosted application.

## Vấn đề
Một người học tự học IELTS từ con số 0 đang gặp phải hai vấn đề cộng hưởng. Thứ nhất là sự phân mảnh: tiến độ học tập, việc ôn từ vựng và nhật ký lỗi sai nằm rải rác ở nhiều công cụ khác nhau, hoặc không được ghi lại ở đâu cả. Thứ hai, nghiêm trọng hơn, là **thiếu nội dung luyện tập thực sự**: một công cụ chỉ theo dõi "hôm nay đã học chưa" không giải quyết được việc mỗi ngày người học vẫn phải tự đi tìm đề Reading, tự tìm audio Listening, tự nghĩ đề Writing/Speaking ở nơi khác — tức là công cụ theo dõi tiến độ không hề làm giảm gánh nặng chuẩn bị bài học hằng ngày, nó chỉ ghi lại kết quả sau khi người học đã tự xoay sở xong. Nếu không có một nơi vừa cung cấp bài luyện tập cụ thể cho cả bốn kỹ năng (Reading/Listening/Writing/Speaking) mỗi ngày, vừa nhắm đúng lỗi sai và từ vựng cá nhân đang yếu, người học rất dễ mất động lực vì tốn thời gian chuẩn bị hơn là luyện tập, lặp lại cùng một lỗi, và để việc ôn từ vựng bị trễ hạn. Riêng với Writing và Speaking, người tự học gần như không có cách nào biết mình đang ở band điểm nào hay cần sửa gì cụ thể nếu không có người chấm.

## Người dùng mục tiêu / Thị trường
Một kỹ sư phần mềm tự học IELTS từ con số 0, muốn học liên tục, đều đặn mỗi ngày, với mục tiêu đạt trình độ tiếng Anh đủ dùng cho công việc chuyên môn. Người này không muốn tốn thời gian mỗi ngày để tự tìm/soạn đề luyện tập — muốn mở app ra là có ngay bài học của hôm nay cho từng kỹ năng. Người này am hiểu công nghệ, muốn toàn quyền kiểm soát và có thể lấy lại dữ liệu học tập của mình bất cứ lúc nào thay vì phụ thuộc vào một SaaS đóng của bên thứ ba, và sẵn sàng tự xây dựng công cụ riêng — kể cả khi điều đó có nghĩa là vận hành cơ sở hạ tầng của chính mình — thay vì thích nghi với một công cụ có sẵn không đúng quy trình học của mình.

## Cơ hội
Các ứng dụng IELTS phổ biến trên thị trường hoặc cung cấp một kho đề tĩnh, soạn sẵn cho số đông (không nhắm đúng điểm yếu của riêng một người học), hoặc chỉ là công cụ theo dõi tiến độ không tự sinh nội dung. Với các mô hình AI hiện đại (qua một nhà cung cấp AI có thể thay thế được, không ràng buộc vĩnh viễn vào một hãng), lần đầu tiên một người học đơn lẻ có thể có một "giáo viên riêng" tự sinh bài luyện tập mới mỗi ngày cho cả bốn kỹ năng, nhắm thẳng vào lỗi sai và từ vựng đang yếu của chính mình — điều mà một kho đề tĩnh không làm được và một gia sư con người không làm được với chi phí tương đương. Là một kỹ sư phần mềm, người dùng mục tiêu có thể tự xây dựng giải pháp này, gọn nhẹ và vừa khít với quy trình học của chính mình, đồng thời vẫn giữ được sự riêng tư và toàn quyền kiểm soát dữ liệu bài làm.

## Mục tiêu
- G-1: Mỗi ngày, người học mở app ra là có ngay một bộ bài luyện tập cụ thể cho cả bốn kỹ năng (Reading, Listening, Writing, Speaking), do AI sinh theo yêu cầu — không cần tự tìm hay chuẩn bị tài liệu ở nơi khác, và không giới hạn ở một lộ trình có ngày kết thúc cố định.
- G-2: Nội dung bài luyện tập mỗi ngày được cá nhân hóa dựa trên lịch sử lỗi sai và từ vựng đến hạn ôn của chính người học, để việc luyện tập luôn nhắm đúng điểm yếu hiện tại thay vì lặp lại ngẫu nhiên hoặc theo một giáo trình cố định.
- G-3: Làm nổi bật các dạng lỗi sai lặp lại ở cả bốn kỹ năng đủ sớm để sửa trước khi chúng trở thành thói quen cố hữu, và để những lỗi đó quay lại làm nguyên liệu cho bài luyện tập kế tiếp (G-2).
- G-4: Duy trì việc ôn từ vựng đều đặn, đúng lịch thông qua phương pháp lặp lại ngắt quãng (spaced repetition), để việc ghi nhớ không phụ thuộc hoàn toàn vào trí nhớ hay ý chí của người học.
- G-5: Hiển thị rõ tiến bộ kỹ năng theo thời gian ở cả bốn kỹ năng — bao gồm cả Writing/Speaking một khi có phản hồi AI — để người học thấy được đà tiến bộ và xác định được điểm yếu nhất của mình.
- G-6: Đảm bảo người học luôn có thể lấy lại toàn bộ dữ liệu học tập của chính mình (bao gồm cả các bài luyện tập đã được sinh ra và kết quả làm bài) dưới một định dạng họ tự đọc/xử lý được, và không bị khoá vĩnh viễn vào một nhà cung cấp hạ tầng hay AI cụ thể nào.
- G-7: Cho người học nhận được phản hồi Writing/Speaking đúng theo tiêu chí chấm điểm IELTS chính thức (Task Response/Achievement, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, và tương ứng cho Speaking), đủ cụ thể để biết chính xác câu/đoạn nào cần sửa — không chỉ một con số band chung chung.
- G-8: Bảo vệ dữ liệu học tập và bài làm cá nhân (đặc biệt là bài Writing/Speaking) khỏi bị truy cập bởi bất kỳ ai khác ngoài chính người học, kể cả khi ứng dụng được host công khai trên Internet.

## Tiêu chí thành công
- Sẵn sàng nội dung mỗi ngày: ≥95% số ngày người học mở app, cả bốn kỹ năng đều đã có bài luyện tập sẵn sàng trước khi họ cần đến, không phải chờ hoặc tự tìm thêm.
- Mức độ cá nhân hóa: ≥50% bài luyện tập Reading/Listening/Writing mới có liên hệ trực tiếp tới ít nhất một lỗi sai gần đây hoặc một từ vựng đến hạn ôn của người học.
- Tính đều đặn trong học tập: người học sử dụng ứng dụng ≥5 ngày/tuần, liên tục trong 12+ tuần.
- Khả năng ghi nhớ từ vựng: ≥80% số từ vựng đến hạn ôn mỗi tuần thực sự được ôn đúng lịch.
- Tính hành động được của lỗi sai: xác định được top 3 nhóm nguyên nhân lỗi sai lặp lại nhiều nhất trước cuối tuần thứ 4, và người học có thể dẫn ra ví dụ cụ thể.
- Khả năng quan sát tiến bộ: xu hướng điểm ở từng kỹ năng có thể quan sát được qua 4+ lần luyện tập/nộp bài trong 8 tuần đầu tiên.
- Chất lượng phản hồi AI: với ≥80% bài Writing được chấm, người học tự đánh giá nhận xét là cụ thể và hữu ích (không phải chung chung/vô nghĩa), dựa trên tự đánh giá của chính người học.
- Tính di động của dữ liệu: có thể xuất toàn bộ dữ liệu học tập (bài luyện tập đã sinh, từ vựng, lỗi sai, bài nộp, điểm) ra một định dạng đọc được, và xác minh không mất dữ liệu, ít nhất một lần.
- Không có sự cố lộ khoá bí mật (API key, thông tin đăng nhập) trong mã nguồn hoặc lịch sử commit, trong suốt vòng đời dự án.

## Không thuộc phạm vi (Non-Goals)
- Các tính năng nhiều người dùng, mạng xã hội, hay cộng tác (bảng xếp hạng, khóa học chia sẻ, đánh giá chéo giữa người học) — đây là công cụ dành cho một người học duy nhất, không phải một LMS thương mại.
- Thương mại hóa dưới bất kỳ hình thức nào (gói trả phí, thuê bao, bán lại quyền truy cập API cho người khác).
- Hệ thống xác thực phức tạp kiểu doanh nghiệp (SSO, phân quyền nhiều vai trò) — chỉ cần đủ để ngăn người lạ truy cập dữ liệu của một người dùng duy nhất.
- Một kho đề tĩnh, soạn sẵn hàng loạt (question bank cố định) — nội dung luyện tập được AI sinh theo yêu cầu mỗi ngày, không phải được biên soạn/nhập trước.
- Một hệ thống mô phỏng thi đầy đủ (full mock test) — trọng tâm là các bài luyện tập nhỏ hằng ngày cho từng kỹ năng và chu trình ôn tập cá nhân, không nhằm tái tạo trải nghiệm thi thật trọn vẹn.
- Đánh giá phát âm (pronunciation) cho Speaking chỉ dựa trên transcript văn bản trong giai đoạn đầu — việc này cần một dịch vụ đánh giá phát âm chuyên biệt, được coi là một quyết định/giai đoạn riêng, không mặc định có ngay.
- Bất kỳ hoạt động marketing, trang giới thiệu (landing page), hay kênh bán hàng công khai nào.
