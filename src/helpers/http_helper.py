from src.helpers.http_client import default_client
import re
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

def extract_doaction_params(html_text: str, search_text: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html_text, 'html.parser')
    results = []
    
    for a_tag in soup.find_all('a'):
        if search_text in a_tag.get_text():
            onclick = a_tag.get('onclick', '')
            if not onclick:
                continue
            
            # doAction('URL', 'CNAME')
            pattern = r"doAction\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
            match = re.search(pattern, onclick)
            
            if match:
                results.append((match.group(1), match.group(2)))
            
    return results

def main(target_ym: str = "202603"):
    base_url = "https://www.jra.go.jp"
    save_dir = Path("data/raw/jra_schedule")
    save_dir.mkdir(parents=True, exist_ok=True)

    print("[1] 初回ページ取得")
    try:
        html1 = default_client.get(base_url)
        if isinstance(html1, bytes):
            html1 = html1.decode('shift_jis', errors='replace')
    except Exception as e:
        print(f"  取得失敗: {e}")
        return

    res1 = extract_doaction_params(html1, "レース結果")
    if not res1:
        print("  [1] 'レース結果' のリンクが見つかりません")
        return
    x1, y1 = res1[0]
    print(f"  [1] 抽出 -> X1={x1}, Y1={y1[:10]}...")

    while True:
        print(f"\n[2] POST 1 (CNAME: {y1[:10]}...)")
        try:
            url2 = base_url + x1
            html2 = default_client.post(url2, data={"cname": y1})
            if isinstance(html2, bytes):
                html2 = html2.decode('shift_jis', errors='replace')
        except Exception as e:
            print(f"  取得失敗: {e}")
            return

        soup2 = BeautifulSoup(html2, 'html.parser')
        current_ym = None
        
        # 年月の抽出
        text_full = soup2.get_text()
        match_date = re.search(r'(\d{4})年(\d{1,2})月', text_full)
        
        if match_date:
            current_ym = f"{match_date.group(1)}{match_date.group(2).zfill(2)}"
        else:
            match_date = re.search(r'(\d{1,2})月', text_full)
            if match_date:
                current_month = int(match_date.group(1))
                current_year = datetime.now().year
                current_ym = f"{current_year}{current_month:02d}"
        
        if not current_ym:
            print("  [2] 現在表示されている年月が見つかりません")
            return

        print(f"  [2] 現在月: {current_ym} (Target: {target_ym})")

        # 保存処理
        save_path2 = save_dir / f"jra_{current_ym}.html"
        save_path2.write_text(html2, encoding="utf-8")
        print(f"  [2] 保存: {save_path2.name}")

        # 終了判定
        if current_ym == target_ym:
            print(f"  [2] 目標月 {target_ym} に到達しました。処理を終了します。")
            return

        # -------------------------------------------------------
        # (3) POST で HTML3 (月別リスト) を取得
        # -------------------------------------------------------
        res2 = extract_doaction_params(html2, "過去レース結果検索")
        if not res2:
            res2 = extract_doaction_params(html2, "過去のレース結果")
            if not res2:
                res2 = extract_doaction_params(html2, "検索")
        
        if not res2:
            print("  [2] '過去レース結果検索' のリンクが見つかりません")
            return
        
        x2, y2 = res2[0]
        
        print(f"\n[3] POST 2 (URL: {x2})")
        try:
            url3 = base_url + x2
            html3 = default_client.post(url3, data={"cname": y2})
            if isinstance(html3, bytes):
                html3 = html3.decode('shift_jis', errors='replace')
        except Exception as e:
            print(f"  取得失敗: {e}")
            return

        soup3 = BeautifulSoup(html3, 'html.parser')
        month_links = []
        
        for a_tag in soup3.find_all('a'):
            text = a_tag.get_text().strip()
            onclick = a_tag.get('onclick', '')
            
            match_date = re.search(r'(\d{4})年(\d{1,2})月', text)
            
            if match_date:
                yymm = f"{match_date.group(1)}{match_date.group(2).zfill(2)}"
                m_cname = re.search(r"doAction\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", onclick)
                if m_cname:
                    month_links.append((yymm, m_cname.group(2), text))
        
        # 降順ソート（最新→最古）
        month_links.sort(key=lambda x: x[0], reverse=True)
        
        # --- 次へ進むCNAMEの決定 ---
        # リストの先頭から順に見ていき、**「現在表示されている月 (`current_ym`) 未満」の月**を見つける
        # 例: current_ym が 202606 の場合、リスト [202607, 202606, 202605, ...] から 202605 を選ぶ
        
        next_cname = None
        next_text_ym = None
        
        for yymm, cname, text in month_links:
            # 現在表示されている月未満（＝過去）の月が見つかったら、それを次とする
            if yymm < current_ym:
                next_cname = cname
                next_text_ym = yymm
                print(f"  [3] 次: {yymm} の CNAME を使用")
                break
        
        if next_cname:
            y1 = next_cname
        else:
            print("  [3] 次が見つかりませんでした。")
            break

if __name__ == '__main__':
    main(target_ym="202603")
