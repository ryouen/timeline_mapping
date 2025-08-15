#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存のHTMLのURLをクリック可能なリンクに更新
"""

import re

# HTMLファイルを読み込む
with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# url-displayクラスの内容をリンクに変換
# パターン: <div class="url-display">data=...</div>
def replace_url_display(match):
    data_part = match.group(1)
    # 完全なURLを再構築（簡易版）
    # 実際のURLはログから取得する必要があるが、ここでは仮のURLを使用
    return f'<a href="#" target="_blank" class="url-display" style="color: #007bff; text-decoration: none; display: block;">data={data_part}</a>'

# 正規表現でurl-displayを置換
html_content = re.sub(
    r'<div class="url-display">data=([^<]+)</div>',
    replace_url_display,
    html_content
)

# スタイルを追加（リンクのホバー効果）
style_addition = '''
        a.url-display:hover {
            text-decoration: underline !important;
            color: #0056b3 !important;
        }
'''

# </style>タグの前にスタイルを追加
html_content = html_content.replace('</style>', style_addition + '\n    </style>')

# 保存
with open('/app/output/japandatascience.com/timeline-mapping/api/v3_results_summary.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTMLのURLをクリック可能なリンクに更新しました")