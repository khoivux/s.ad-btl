import google.generativeai as genai
from django.conf import settings
from ..ai_core.neo4j_db import neo4j_db

from ..ai_core.neo4j_db import neo4j_db


class ConsultantAgent:
    def __init__(self):
        pass

    def get_advice_stream(self, user_id, user_message, chat_history_list=None):
        # Ensure latest key is used
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('models/gemini-flash-latest')

        # 1. Persona and Context
        print(f"[AI-LOG] Fetching GraphRAG and LSTM context for user {user_id}...")
        
        # 1.1 Fetch real-time customer context from customer-service
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
            
            # --- NEURAL LSTM RANKING ---
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
                    f"- {r['title']}{format_domain(r)} (Match: {r['score']}đ)\n  MÔ TẢ: {r['description'][:200]}..." 
                    for r in ai_recs
                ])
                print(f"[AI-LOG] AI LSTM Pool of products ready with domain details.")
            
            # --- KNOWLEDGE GRAPH TRIPLETS ---
            graph_triples = neo4j_db.get_direct_interactions_context(user_id)
            triples_context = "\n".join([
                f"- Khách hàng đã {t['action']} sản phẩm '{t['title']}'."
                for t in graph_triples
            ])
            if not triples_context: triples_context = "Chưa có hành vi cụ thể (khách mới)."
            
            kb_context = f"DỰA TRÊN LSTM SEQUENTIAL RECS:\n{recom_context}\n\nLỊCH SỬ KNOWLEDGE GRAPH:\n{triples_context}"
        except Exception as e:
            print(f"[AI-LOG] Failed LSTM or Graph retrieval: {e}")
            kb_context = "Hệ thống tri thức tạm thời gián đoạn."

        # --- SEMANTIC VECTOR DB SEARCH (RAG) ---
        rag_context = ""
        try:
            from ..ai_core.vector_db import vector_db
            print(f"[AI-LOG] 🔍 Querying vector DB for query: {user_message}")
            rag_results = vector_db.query(user_message, n_results=3)
            
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

        # 3. History
        history_text = ""
        if isinstance(chat_history_list, list):
            for m in chat_history_list:
                role = "Khách" if m.get('role') == 'user' else "AI"
                history_text += f"{role}: {m.get('content')}\n"

        # 4. Prompt
        print(f"[AI-LOG] Generating natural prompt for user {user_id}.")
        
        rag_section = ""
        if rag_context:
            rag_section = f"\nTÀI LIỆU HƯỚNG DẪN & CHÍNH SÁCH CỬA HÀNG:\n---\n{rag_context}\n---"

        system_prompt = f"""Bạn là một chuyên gia tư vấn sản phẩm tận tâm của cửa hàng MicroStore với hơn 20 năm kinh nghiệm thấu hiểu khách hàng.

NHIỆM VỤ CỦA BẠN:
1. Trò chuyện như một NGƯỜI BẠN đang giới thiệu về những sản phẩm chất lượng, KHÔNG PHẢI một cỗ máy đang báo cáo kết quả.
2. TUYỆT ĐỐI CẤM (BLACKLIST): 'Điểm tương thích', 'Match', 'Lọc ra', 'Tầm giá', 'Kết quả', 'Đề xuất dựa trên...', 'Hệ thống đã chọn'.
3. PHONG CÁCH TƯ VẤN:
   - Hãy nói một cách tự nhiên nhất: 'Tôi vừa tìm thấy món này hay lắm...', 'Có 3 sản phẩm này tôi tin bạn sẽ rất thích...', 'Với khoảng $7, bạn có thể sở hữu ngay...'.
   - Giải thích lý do bằng cách DÙNG LỊCH SỬ KNOWLEDGE GRAPH (ví dụ: 'Thấy bạn vừa xem sản phẩm A, mình nghĩ sản phẩm B này rất hợp vì...').
   - Sử dụng các tài liệu hướng dẫn và chính sách được cung cấp để trả lời các câu hỏi về chính sách, phí ship, bảo hành hoặc mẹo mua sắm của cửa hàng một cách chính xác.
   - Lời chào ngắn gọn (tối đa 1 câu). Không rườm rà.

QUY TẮC PHỤC VỤ (BÍ MẬT):
- Luôn ưu tiên các sản phẩm đầu trong danh sách 'AI RECOMMENDS' trừ khi khách yêu cầu cụ thể hoặc đang hỏi về các chủ đề khác.
- Chỉ tư vấn những sản phẩm có trong danh sách được cung cấp hoặc trả lời các thông tin chính sách từ tài liệu.

DỮ LIỆU BỐI CẢNH (CHỈ DÙNG ĐỂ THẤU HIỂU, KHÔNG ĐƯỢC CHÉP LẠI):
---
HỒ SƠ KHÁCH HÀNG: {persona}{rag_section}
DANH SÁCH GỢI Ý & GRAPH:
{kb_context}
---

LỊCH SỬ TRÒ CHUYỆN:
{history_text}

HÃY BẮT ĐẦU TƯ VẤN NGAY (Bằng Tiếng Việt, ấm áp và lôi cuốn):
"""
        full_prompt = f"{system_prompt}\n\nKhách: {user_message}\nAI:"
        
        # 5. Stream output word by word for 'typing' effect
        try:
            print(f"[AI-LOG] Calling genai.generate_content...")
            response = self.model.generate_content(full_prompt, stream=True)
            print(f"[AI-LOG] Stream response received. Starting iteration...")
            import time
            for chunk in response:
                if chunk.text:
                    print(f"[AI-LOG] Chunk: {chunk.text[:15]}...")
                    words = chunk.text.split(' ')
                    for i, word in enumerate(words):
                        space = ' ' if i < len(words) - 1 else ''
                        yield word + space
                        time.sleep(0.01)
            print(f"[AI-LOG] Stream finished successfully.")

        except Exception as e:
            print(f"[STREAM ERROR] Fallback triggered due to: {e}")
            yield "Chào bạn! Thành thật xin lỗi vì hệ thống đang gặp chút gián đoạn kỹ thuật nhỏ. Hãy thử lại sau ít phút nhé!"

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
