import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import base64
# ページ設定
st.set_page_config(page_title="英単語テスト", layout="centered")
# --- 音声再生用の関数 ---
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    os.remove("temp.mp3")
# --- スタイル設定 ---
st.markdown("""
    <style>
    .word-box { background-color: #f0f2f6; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 10px; border: 2px solid #ddd; position: relative;}
    .hint-box { background-color: #fff3cd; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; color: #856404; }
    .stButton>button { height: 3em; font-size: 18px; border-radius: 10px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)
# セッション状態の初期化
if 'status' not in st.session_state:
    st.session_state.status = 'setting'
    st.session_state.results = {'〇': [], '△': [], '×': []}
# --- 1 & 2: 設定画面 ---
if st.session_state.status == 'setting':
    st.title("📚 チェックテストを始める")
    
    book_options = {
        "ターゲット1900": "target1900.csv",
        "ターゲット1400":"target1400.csv",
        "ターゲット1200":"target1200.csv",
        "ターゲット1000":"target1000.csv",
        "システム英単語": "sis-tan.csv",
        "LEAP": "leap.csv",
        "LEAP(旧)":"leaped.csv",
        "速読英単語必修編": "sokutan2.csv",
        "速読英熟語": "sokuzyuku.csv",
        "いろはにほへと":"いろはに.csv"
    }
    
    selected_book_name = st.selectbox("1: 本を選ぶ", list(book_options.keys()))
    csv_filename = book_options[selected_book_name]
    
    st.write("2: テスト範囲指定")
    col1, col2 = st.columns(2)
    start_no = col1.number_input("開始番号", value=1, min_value=1)
    end_no = col2.number_input("終了番号", value=100, min_value=1)
    
    if st.button("3: 単語テスト実行！"):
        try:
            current_dir = os.path.dirname(__file__)
            csv_path = os.path.join(current_dir, csv_filename)
            
            df = pd.read_csv(csv_path, names=["no", "english", "japanese","hint"])
            mask = (df['no'] >= start_no) & (df['no'] <= end_no)
            target_words = df.loc[mask].to_dict('records')
            
            if not target_words:
                st.error("その範囲に単語がありません！CSVの中身を確認してください。")
            else:
                st.session_state.test_list = random.sample(target_words, len(target_words))
                st.session_state.current_idx = 0
                st.session_state.show_ans = False
                st.session_state.show_hint = False
                st.session_state.status = 'testing'
                st.rerun()
        except Exception as e:
            st.error(f"ファイルが見つかりません。{csv_filename} を作成してください。")
            
# --- 3: テスト画面 ---
elif st.session_state.status == 'testing':
    q = st.session_state.test_list[st.session_state.current_idx]
    st.title("📖 テスト")
    
    # 画面を「左：メイン表示（8）」と「右：操作ボタン（2）」に分割
    col_main, col_ctrl = st.columns([8, 2])
    
    # --- 左側：問題と回答の表示 ---
    with col_main:
        # 英単語
        st.markdown(f"<div class='word-box'><h1>{q['english']}</h1></div>", unsafe_allow_html=True)
        
        # ヒント表示（フラグが立っている時のみ）
        if st.session_state.show_hint:
            st.markdown(f"<div class='hint-box'>{q['hint']}</div>", unsafe_allow_html=True)
        else:
            st.write("") # スペース確保
            
        # 答え表示（フラグが立っている時のみ）
        if st.session_state.show_ans:
            st.markdown(f"<div class='word-box' style='background-color:#e1f5fe;'><h2>{q['japanese']}</h2></div>", unsafe_allow_html=True)
        else:
            # 答えが出ていない時は高さを維持するための空のボックスなど
            st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)

    # --- 右側：すべての操作ボタン ---
    with col_ctrl:
        # 音声
        if st.button("🔊 音声"):
            speak(q['english'])
        
        st.write("---") # 区切り線
        
        # 答えを見る / 一言ヒント
        if not st.session_state.show_ans:
            if st.button("👁️ 答え"):
                st.session_state.show_ans = True
                st.rerun()
        
        if not st.session_state.show_hint:
            if st.button("💡 一言"):
                st.session_state.show_hint = True
                st.rerun()

        st.write("---") # 区切り線
        
        # 判定ボタン
        if st.button("〇"):
            st.session_state.results['〇'].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list): st.session_state.status = 'result'
            st.rerun()
            
        if st.button("△"):
            st.session_state.results['△'].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list): st.session_state.status = 'result'
            st.rerun()
            
        if st.button("×"):
            st.session_state.results['×'].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list): st.session_state.status = 'result'
            st.rerun()
            
        st.write("---")
        if st.button("中止"):
            st.session_state.status = 'result'
            st.rerun()


# --- 4: 結果画面（格子レイアウト版） ---
elif st.session_state.status == 'result':
   st.title("📊 復習リスト")

   # 理想のレイアウトに合わせて列を作成
   col_left, col_right = st.columns(2)

   # 左側：△ 要確認
   with col_left:
       st.markdown("<div class='grid-header'>△</div>", unsafe_allow_html=True)
       if st.session_state.results['△']:
           html = "<div class='grid-container'>"
           for i in st.session_state.results['△']:
               # 英語／日本語 の形式
               html += f"<div class='grid-item'>{i['english']} ／ {i['japanese']}</div>"
           html += "</div>"
           st.markdown(html, unsafe_allow_html=True)
       else:
           st.write("なし")

   # 右側：× 苦手
   with col_right:
       st.markdown("<div class='grid-header'>×</div>", unsafe_allow_html=True)
       if st.session_state.results['×']:
           html = "<div class='grid-container'>"
           for i in st.session_state.results['×']:
               # 英語／日本語 の形式
               html += f"<div class='grid-item'>{i['english']} ／ {i['japanese']}</div>"
           html += "</div>"
           st.markdown(html, unsafe_allow_html=True)
       else:
           st.write("なし")

   st.write("---")
   if st.button("最初に戻る"):
       st.session_state.clear()
       st.rerun()
