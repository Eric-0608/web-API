from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def 查詢單字_API():

    查詢單字 = request.args.get('q', '').strip().lower()
    
    if not 查詢單字:
        return jsonify({'error': '請提供單字'})

    連線 = sqlite3.connect('我的單字本.db')
    滑鼠 = 連線.cursor()

    滑鼠.execute('''
    CREATE TABLE IF NOT EXISTS 單字表 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        單字 TEXT NOT NULL,
        解釋 TEXT NOT NULL
    )
    ''')

    回傳_解釋 = ""
    回傳_來源 = ""

    滑鼠.execute('SELECT 單字, 解釋 FROM 單字表 WHERE 單字 = ?', (查詢單字,))
    查詢結果 = 滑鼠.fetchall()

    if 查詢結果:
        for 一筆資料 in 查詢結果:
            回傳_解釋 = 一筆資料[1]
            回傳_來源 = "資料庫"
    else:
        網址 = f"https://dictionary.cambridge.org/zht/詞典/英語-漢語-繁體/{查詢單字}"
        偽裝瀏覽器標頭 = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            回應 = requests.get(網址, headers=偽裝瀏覽器標頭)
            
            if 回應.status_code == 200:
                網頁解析器 = BeautifulSoup(回應.text, "html.parser")
                解釋標籤 = 網頁解析器.select_one(".def-body .trans")
                
                if 解釋標籤:
                    中文解釋 = 解釋標籤.get_text().strip()
                    滑鼠.execute('INSERT INTO 單字表 (單字, 解釋) VALUES (?, ?)', (查詢單字, 中文解釋))
                    連線.commit() 
                    回傳_解釋 = 中文解釋
                    回傳_來源 = "網路來源 (已自動存入資料庫)"
                else:
                    回傳_解釋 = "網路上查不到這個字。"
                    回傳_來源 = "錯誤"
            else:
                回傳_解釋 = "網路連線失敗。"
                回傳_來源 = "錯誤"

        except:
            回傳_解釋 = "連線錯誤。"
            回傳_來源 = "錯誤"

    連線.close()

    
    if 回傳_來源 == "錯誤":
        return jsonify({'error': 回傳_解釋}), 404
    else:
        return jsonify({
            'word': 查詢單字,
            'definition': 回傳_解釋,
            'source': 回傳_來源
        })

# === 啟動伺服器 ===
if __name__ == '__main__':
    print("=== 單字查詢系統 (網頁版) 啟動 ===")
    app.run(port=5000, debug=True)