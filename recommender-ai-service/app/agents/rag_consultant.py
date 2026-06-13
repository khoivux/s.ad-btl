import google.generativeai as genai
import requests
from django.conf import settings
from ..ai_core.neo4j_db import neo4j_db


class ConsultantAgent:
    def __init__(self):
        pass

    def get_advice_stream(self, user_id, user_message, chat_history_list=None):
        # Ensure latest key is used
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

        # 1. Persona and Context
        print(f"[AI-LOG] Fetching GraphRAG and LSTM context for user {user_id}...")
        
        # --- NGUỒN 1: HỒ SƠ KHÁCH HÀNG (CUSTOMER PROFILE) ---
        # Gọi HTTP API sang 'user-service' để lấy thông tin điểm tích lũy và hạng thành viên hiện tại của khách hàng.
        points, level_id = 0, 1
        try:
            import requests
            cust_r = requests.get(f"http://user-service:8000/users/{user_id}/", timeout=5)
            if cust_r.status_code == 200:
                c_data = cust_r.json()
                wallet = c_data.get('wallet', {})
                points = wallet.get('usable_points', 0)
                level_id = wallet.get('current_level', {}).get('id', 1)
        except Exception as e:
            print(f"[AI-LOG] Behavioral context failed: {e}")

        persona = f"Khách hàng số #{user_id} (Hạng thẻ {level_id}, tích lũy {points} điểm). Người quan tâm đến MicroStore."

        # R. Graph-Based Retrieval & LSTM Prediction
        try:
            from ..ai_core.behavior_trainer import behavior_trainer
            
            # --- NGUỒN 2: DỰ ĐOÁN CHUỖI HÀNH VI LSTM (NEURAL LSTM RANKING) ---
            # Gọi bộ huấn luyện LSTM để lấy ra danh sách các sản phẩm tiếp theo được đề xuất riêng cho khách hàng này.
            print(f"[AI-LOG] 🧠 Identifying Sequential Gems via LSTM for User {user_id}...")
            ai_recs = behavior_trainer.get_sequential_recommendations(user_id, top_k=20)
            
            recom_context = ""
            if ai_recs:
                def format_domain(r):
                    dtype = r.get('product_type', 'General')
                    ddata = r.get('domain_data', {})
                    if not ddata: return ""
                    
                    details = []
                    for k, v in ddata.items():
                        details.append(f"{k.replace('_', ' ').capitalize()}: {v}")
                    return f" [{dtype} - {', '.join(details)}]"

                recom_context = "\n".join([
                    f"- {r['title']} (Mã/ID: {r['id']}){format_domain(r)} (Match: {r['score']}đ)\n  MÔ TẢ: {r['description'][:200]}..." 
                    for r in ai_recs
                ])
                print(f"[AI-LOG] AI LSTM Pool of products ready with domain details.")
            
            # --- NGUỒN 3: ĐỒ THỊ TRI THỨC NEO4J (KNOWLEDGE GRAPH TRIPLETS) ---
            # Truy vấn cơ sở dữ liệu đồ thị Neo4j để lấy ra 5 hành vi tương tác (view/purchase/wishlist...) gần nhất của khách hàng.
            graph_triples = neo4j_db.get_direct_interactions_context(user_id)
            triples_context = "\n".join([
                f"- Khách hàng đã {t['action']} sản phẩm '{t['title']}' (Mã/ID: {t['product_id']})."
                for t in graph_triples
            ])
            if not triples_context: triples_context = "Chưa có hành vi cụ thể (khách mới)."
            
            # --- KIỂM TRA LỊCH SỬ MUA SẮM THỰC TẾ TRONG NEO4J ---
            purchased_titles = []
            try:
                with neo4j_db.driver.session() as session:
                    purch_res = session.run(
                        "MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product) RETURN p.title as title",
                        user_id=int(user_id)
                    )
                    purchased_titles = list(set([r["title"] for r in purch_res if r["title"] and isinstance(r["title"], str)]))
            except Exception as pe:
                print(f"[AI-LOG] Failed to query Neo4j purchases: {pe}")
            
            purchased_status = f"Đã mua các sản phẩm: {', '.join(purchased_titles)}" if purchased_titles else "Chưa mua sản phẩm nào"
            
            # --- TRUY VẤN DANH SÁCH ĐƠN HÀNG CHI TIẾT TỪ ORDER-SERVICE ---
            orders_context = ""
            try:
                orders_resp = requests.get(f"http://order-service:8000/orders/?customer_id={user_id}", timeout=5)
                if orders_resp.status_code == 200:
                    orders_data = orders_resp.json().get('results', [])
                    if orders_data:
                        order_summaries = []
                        for idx, order in enumerate(orders_data[:5]): # Lấy tối đa 5 đơn hàng gần nhất
                            items_str = ", ".join([f"{item['product_name']} (x{item['quantity']})" for item in order.get('items', [])])
                            created_time = order.get('created_at', '')[:10]
                            order_summaries.append(
                                f"- Đơn hàng #{order['id']} ({created_time}): Trạng thái '{order['status']}', Tổng tiền: {order['total_amount']}$, Sản phẩm: [{items_str}]"
                            )
                        orders_context = "\n".join(order_summaries)
                    else:
                        orders_context = "Chưa có đơn hàng nào."
                else:
                    orders_context = "Không thể lấy thông tin đơn hàng từ hệ thống."
            except Exception as oe:
                print(f"[AI-LOG] Failed to fetch orders from order-service: {oe}")
                orders_context = "Lỗi kết nối hệ thống đơn hàng."

            kb_context = f"DỰA TRÊN LSTM SEQUENTIAL RECS:\n{recom_context}\n\nLỊCH SỬ KNOWLEDGE GRAPH:\n{triples_context}\n\nLỊCH SỬ MUA SẮM THỰC TẾ (NEO4J): {purchased_status}\n\nDANH SÁCH ĐƠN HÀNG CHI TIẾT (ORDER-SERVICE):\n{orders_context}"
        except Exception as e:
            print(f"[AI-LOG] Failed LSTM or Graph retrieval: {e}")
            kb_context = "Hệ thống tri thức tạm thời gián đoạn."

        # --- NGUỒN 4: CƠ SỞ DỮ LIỆU VECTOR CHROMADB (SEMANTIC VECTOR DB SEARCH - RAG) ---
        # Sử dụng ChromaDB để tìm các tài liệu tĩnh (cẩm nang, chính sách) hoặc thông tin sản phẩm có độ tương đồng cao nhất với câu hỏi hiện tại.
        rag_context = ""
        try:
            from ..ai_core.vector_db import vector_db
            
            # Tối ưu truy vấn RAG cho các câu trả lời ngắn/hội thoại (như "có", "không", "ok")
            search_query = user_message
            if chat_history_list and len(user_message.strip()) < 12:
                conversational_words = {"có", "không", "ok", "yes", "no", "được", "chưa", "tiếp", "cảm ơn", "cám ơn", "thanks", "thank", "dạ", "ừ", "uh", "okey", "okay"}
                clean_msg = user_message.strip().lower().strip("?.! ")
                if clean_msg in conversational_words or len(clean_msg) < 4:
                    last_assistant_msg = ""
                    for msg in reversed(chat_history_list):
                        if msg.get('role') == 'assistant':
                            last_assistant_msg = msg.get('content', '')
                            break
                    if last_assistant_msg:
                        import re
                        clean_assistant = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', last_assistant_msg)
                        clean_assistant = re.sub(r'<[^>]+>', '', clean_assistant)
                        search_query = f"{clean_assistant[:150]} {user_message}"

            print(f"[AI-LOG] 🔍 Querying vector DB for query: {search_query}")
            rag_results = vector_db.query(search_query, n_results=3)
            
            if rag_results and 'documents' in rag_results and rag_results['documents']:
                matched_docs = []
                for doc, meta, dist in zip(
                    rag_results['documents'][0], 
                    rag_results['metadatas'][0], 
                    rag_results['distances'][0]
                ):
                    print(f"[AI-LOG] RAG Match: {meta.get('source', meta.get('title', 'Unknown'))} | L2 Distance: {dist:.4f}")
                    if dist < 0.85:
                        matched_docs.append(doc)
                
                if matched_docs:
                    rag_context = "\n\n".join(matched_docs)
                    print(f"[AI-LOG] Found {len(matched_docs)} relevant RAG documents.")
                else:
                    print(f"[AI-LOG] No RAG documents below distance threshold.")
        except Exception as e:
            print(f"[AI-LOG] Failed Vector DB query: {e}")

        # --- NGUỒN 5: LỊCH SỬ CUỘC TRÒ CHUYỆN (CHAT HISTORY) ---
        # Duyệt qua danh sách tin nhắn cũ trong phiên hội thoại hiện tại để tạo tính liên kết cho câu trả lời.
        history_text = ""
        if isinstance(chat_history_list, list):
            # Lấy tối đa 15 tin nhắn gần nhất để giữ cuộc hội thoại tập trung và hiệu năng tốt
            recent_history = chat_history_list[-15:]
            for m in recent_history:
                role = "Khách" if m.get('role') == 'user' else "AI"
                history_text += f"{role}: {m.get('content')}\n"

        # 4. Prompt
        print(f"[AI-LOG] Generating natural prompt for user {user_id}. History size: {len(chat_history_list) if chat_history_list else 0}")
        
        rag_section = ""
        if rag_context:
            rag_section = f"\nTÀI LIỆU HƯỚNG DẪN & CHÍNH SÁCH CỬA HÀNG:\n---\n{rag_context}\n---"

        system_instructions = f"""Bạn là một chuyên gia tư vấn sản phẩm tận tâm của cửa hàng MicroStore với hơn 20 năm kinh nghiệm thấu hiểu khách hàng.

NHIỆM VỤ CỦA BẠN:
1. Trò chuyện như một NGƯỜI BẠN đang giới thiệu về những sản phẩm chất lượng, KHÔNG PHẢI một cỗ máy đang báo cáo kết quả.
2. TUYỆT ĐỐI CẤM (BLACKLIST): 'Điểm tương thích', 'Match', 'Lọc ra', 'Tầm giá', 'Kết quả', 'Đề xuất dựa trên...', 'Hệ thống đã chọn'.
3. PHONG CÁCH TƯ VẤN & BÁM SÁT NGỮ CẢNH:
   - Hãy nói một cách tự nhiên nhất: 'Tôi vừa tìm thấy món này hay lắm...', 'Có 3 sản phẩm này tôi tin bạn sẽ rất thích...', 'Với khoảng $7, bạn có thể sở hữu ngay...'.
   - Giải thích lý do bằng cách DÙNG LỊCH SỬ KNOWLEDGE GRAPH (ví dụ: 'Thấy bạn vừa xem sản phẩm A, mình nghĩ sản phẩm B này rất hợp vì...').
   - Sử dụng các tài liệu hướng dẫn và chính sách được cung cấp để trả lời các câu hỏi về chính sách, phí ship, bảo hành hoặc mẹo mua sắm của cửa hàng một cách chính xác.
   - CHỈ chào hỏi khách ở câu thoại đầu tiên. Ở các tin nhắn tiếp theo trong cùng hội thoại, TUYỆT ĐỐI KHÔNG lặp lại các câu chào như 'Chào bạn!', 'Hi!',... để cuộc trò chuyện tự nhiên và thân thiện.
   - Khi khách hỏi về lịch sử mua sắm/chi tiêu hoặc các đơn hàng đã đặt, bạn TUYỆT ĐỐI KHÔNG dựa vào số điểm tích lũy (ví dụ: 0 điểm) để khẳng định khách chưa mua sắm (vì điểm có thể đã tiêu dùng hoặc chưa đồng bộ). Thay vào đó, hãy luôn kiểm tra mục 'LỊCH SỬ MUA SẮM THỰC TẾ (NEO4J)' và 'DANH SÁCH ĐƠN HÀNG CHI TIẾT (ORDER-SERVICE)' ở phần bối cảnh. Nếu các mục này ghi nhận có sản phẩm hoặc đơn hàng đã mua, hãy nhiệt tình liệt kê chi tiết các sản phẩm đó và trạng thái đơn hàng của chúng. Nếu ghi nhận 'Chưa mua sản phẩm nào' hoặc 'Chưa có đơn hàng nào', bạn mới trả lời lịch sự là chưa ghi nhận dữ liệu giao dịch trên hệ thống.
   - **Bám sát câu thoại liền trước và Đối tượng người dùng:** Khi khách hàng đặt câu hỏi tiếp theo (ví dụ: "còn sản phẩm nào khác không"), bạn phải phân tích cuộc trò chuyện để tiếp tục giới thiệu các sản phẩm liên quan đến nhu cầu vừa được thảo luận ở lượt thoại ngay trước đó (ví dụ: đồ chơi trẻ em). Tuyệt đối không nhảy cóc sang chủ đề từ nhiều lượt thoại trước.
   - **Tư vấn phù hợp đối tượng (Độ tuổi/Nhu cầu):** Nếu khách hàng đang tìm sản phẩm cho trẻ em (hoặc con cái giải trí), hãy chỉ chọn lọc các sản phẩm phù hợp như đồ chơi (`Toys`), cờ tỷ phú, sách thiếu nhi. Tuyệt đối không đề xuất các sản phẩm nặng nề dành cho người lớn như tiểu thuyết viễn tưởng xã hội đen tối `1984`.
   - **Đọc đúng Loại sản phẩm (Product Type):** Ví dụ Bạn chỉ được phép gọi một sản phẩm là "sách" nếu nó thuộc danh mục `Book`. Nếu thuộc danh mục `Toys`, hãy gọi nó là "đồ chơi". Tuyệt đối không gộp chung các sản phẩm khác loại rồi gọi chung là sách.

4. QUY TẮC ĐỊNH DẠNG TÊN SẢN PHẨM:
   - Khi giới thiệu hay nhắc đến tên của bất kỳ sản phẩm nào có trong danh sách gợi ý hoặc bối cảnh, hãy LUÔN LUÔN định dạng tên sản phẩm dưới dạng liên kết Markdown bằng cách sử dụng chính xác ID sản phẩm tương ứng được cung cấp: [Tên sản phẩm](/products/ID/) (Ví dụ: [Atomic Habits](/products/118/), [Curry 10](/products/206/)).
   - Điều này giúp khách hàng có thể bấm trực tiếp vào tên sản phẩm để xem chi tiết trang sản phẩm đó.
   - TUYỆT ĐỐI KHÔNG tự bịa ra ID sản phẩm khác ngoài các ID đã được cung cấp trong danh sách gợi ý và bối cảnh. Chỉ dùng liên kết cho các sản phẩm thực tế có ID rõ ràng.

QUY TẮC PHỤC VỤ (BÍ MẬT):
- Luôn ưu tiên các sản phẩm đầu trong danh sách 'AI RECOMMENDS' trừ khi khách yêu cầu cụ thể hoặc đang hỏi về các chủ đề khác.
- Chỉ tư vấn những sản phẩm có trong danh sách được cung cấp hoặc trả lời các thông tin chính sách từ tài liệu.

DỮ LIỆU BỐI CẢNH (CHỈ DÙNG ĐỂ THẤU HIỂU, KHÔNG ĐƯỢC CHÉP LẠI):
---
HỒ SƠ KHÁCH HÀNG: {persona}{rag_section}
DANH SÁCH GỢI Ý & GRAPH:
{kb_context}
---
"""

        # Build clean sequential conversation block
        conversation_block = "CUỘC TRÒ CHUYỆN ĐANG DIỄN RA:\n"
        if history_text:
            conversation_block += history_text
        conversation_block += f"Khách: {user_message}\nAI:"

        full_prompt = f"""{system_instructions}

YÊU CẦU: Hãy bám sát diễn biến hội thoại và dữ liệu bối cảnh ở trên để phản hồi tin nhắn mới nhất của Khách (bằng tiếng Việt, ấm áp, thân thiện và lôi cuốn).

{conversation_block}"""
        
        # 5. Stream output word by word for 'typing' effect
        try:
            print(f"[AI-LOG] Calling genai.generate_content...")
            response = self.model.generate_content(full_prompt, stream=True)
            print(f"[AI-LOG] Stream response received. Starting iteration...")
            import time
            for chunk in response:
                try:
                    # Check if candidates and parts exist to prevent ValueError on metadata-only chunks
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        text = chunk.text
                        if text:
                            print(f"[AI-LOG] Chunk: {text[:15]}...")
                            words = text.split(' ')
                            for i, word in enumerate(words):
                                space = ' ' if i < len(words) - 1 else ''
                                yield word + space
                                time.sleep(0.01)
                except (ValueError, IndexError, AttributeError):
                    pass
            print(f"[AI-LOG] Stream finished successfully.")

        except Exception as e:
            print(f"[STREAM ERROR] Fallback triggered due to: {e}")
            yield " Thành thật xin lỗi vì hệ thống đang gặp chút gián đoạn kỹ thuật nhỏ. Hãy thử lại sau ít phút nhé!"

    def get_advice(self, user_id, user_message, chat_history_list=None):
        try:
            full_advice = ""
            for chunk in self.get_advice_stream(user_id, user_message, chat_history_list):
                full_advice += chunk
            return full_advice
        except Exception as e:
            print(f"[CHAT ERROR] {e}")
            return "Tôi xin lỗi, 'bộ não' AI hiện đang có vấn đề."

# Singleton
consultant_agent = ConsultantAgent()
