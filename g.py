import sys
import os
import markdown
from datetime import datetime
from markdown.extensions.codehilite import CodeHiliteExtension
from collections import defaultdict
from xml.sax.saxutils import escape
from dateutil import parser

# 配置路径
POSTS_DIR = 'posts'
DIST_DIR = 'dist'
# RSS
SITE_URL = "https://iamzhz.github.io/zolog"
SITE_TITLE = "iamzhz zolog"
SITE_DESCRIPTION = "iamzhz 的 blog"
RSS_MAX_ITEMS = 10  # 最多输出的篇数

html_head = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iamzhz | {}</title>
    <link rel="stylesheet" href="styles.css"></head>
<body>
    <div class="glow-cursor" id="glowCursor"></div>
    <nav class="shiro-nav">
        <a href="#" class="nav-brand">iamzhz<span>.</span></a>
        
        <div style="position: relative;">
            <div class="nav-highlight" id="navHighlight"></div>
            <ul class="nav-links" id="navLinks">
                <li><a href="index.html" class="{}">首页</a></li>
                <li><a href="tags.html" class="{}">标签云</a></li>
                <li><a href="about.html" class="{}">关于</a></li>
            </ul>
        </div>
        
        <div class="nav-actions"></div>
    </nav>
    
    <main class="main-container">
        <div class="content-area">
"""
html_tail = """
        </div>
    </main>
    
    <footer class="site-footer">
        <div class="footer-content">
            <p>Powered by iamzhz</p>
        </div>
    </footer>
    <script src="script.js"></script>
</body>
</html>
"""

def get_file_content(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Cannot open file `{filename}`! Error: {e}")
        return ""

def process_single_post(full_path: str):
    md = markdown.Markdown(extensions=[
        'tables', 'meta', 'fenced_code', 'toc',
        CodeHiliteExtension(linenums=True)
    ])
    
    # 1. 读取内容
    content = get_file_content(full_path)
    if not content: return None
    body_html = md.convert(content)
    
    # 2. 提取文件名 (例如从 'posts/tech/python.md' 提取出 'python')
    base_name = os.path.basename(full_path) # python.md
    file_slug = base_name.replace('.md', '') # python
    output_filename = file_slug + '.html'    # python.html

    # 3. 提取元数据
    meta = getattr(md, 'Meta', {})
    title = meta.get('title', [None])[0]
    if not title:
        title = md.toc_tokens[0]['name'] if md.toc_tokens else file_slug
    
    date_str = meta.get('date', ['2026-01-01'])[0]
    try:
        dt_obj = parser.parse(date_str)
    except:
        # 解析失败则使用一个默认日期（例如 2026-01-01 00:00）
        dt_obj = datetime(2026, 1, 1, 0, 0, 0)

    show_update_meta = meta.get('show-update', ['true'])[0].lower()
    show_update = show_update_meta in ('true', '1', 'yes', 'on')

    # 4. 生成 HTML
    # 判断是否是 about 页面（假设 about.md 可能在任何目录下）
    is_about = file_slug == 'about'
    format_args = (title, '', '', 'active') if is_about else (title, 'active', '', '')
    
    full_html = html_head.format(*format_args) + body_html + html_tail
    
    # 5. 统一写入 dist 根目录
    with open(os.path.join(DIST_DIR, output_filename), 'w', encoding='utf-8') as f:
        f.write(full_html)

    return {
        'title': title,
        'date': dt_obj,
        'description': meta.get('description', ['暂无描述'])[0],
        'tags': meta.get('tags', []),
        'url': output_filename,
        'body_html': body_html,
        'show_update': show_update
    }

def generate_index_and_tags(all_posts):
    """汇总生成 index.html 和 tags.html"""
    
    # --- 1. 生成主页 (Index) ---
    # 按日期降序排列
    all_posts.sort(key=lambda x: x['date'], reverse=True)
    
    index_body = "<h1>最近更新</h1><div class='post-list'>"
    for post in all_posts:
        tag_spans = "".join([f"<span class='tag-mini'>{t}</span>" for t in post['tags']])
        index_body += f"""
        <article class="post-item">
            <h2><a href="{post['url']}">{post['title']}</a></h2>
            <div class="meta-info">{post['date'].strftime('%Y-%m-%d')} | {tag_spans}</div>
            <p>{post['description']}</p>
        </article>
        """
    index_body += "</div>"
    
    with open(os.path.join(DIST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_head.format("首页", 'active', '', '') + index_body + html_tail)

    # --- 2. 生成标签页 (Tags) ---
    tag_map = defaultdict(list)
    for post in all_posts:
        for t in post['tags']:
            tag_map[t].append(post)

    tags_body = "<h1>标签云</h1>"
    for tag, posts in tag_map.items():
        tags_body += f"<section><h3># {tag}</h3><ul>"
        for p in posts:
            tags_body += f'<li><a href="{p["url"]}">{p["title"]}</a> ({p["date"].strftime("%m-%d")})</li>'
        tags_body += "</ul></section>"

    with open(os.path.join(DIST_DIR, 'tags.html'), 'w', encoding='utf-8') as f:
        f.write(html_head.format("标签汇总", '', 'active', '') + tags_body + html_tail)

def generate_rss(posts_data, site_url, site_title, site_description):
    """生成 RSS 2.0 格式的 feed.xml，包含全文内容，时间使用 UTC+8"""
    filtered_posts = [p for p in posts_data if p.get('show_update', True)]
    posts_sorted = sorted(filtered_posts, key=lambda x: x['date'], reverse=True)
    posts_sorted = posts_sorted[:RSS_MAX_ITEMS]
    items_xml = ""

    for post in posts_sorted:
        link = f"{site_url.rstrip('/')}/{post['url']}"

        # ----- 修改点1：发布时间使用北京时间（+0800）-----
        # post['date'] 是一个 datetime 对象（不含时区），其时间部分为 00:00:00
        # 我们直接把它当作北京时间，并格式化为 RFC 822 格式
        pub_date = post['date'].strftime("%a, %d %b %Y %H:%M:%S +0800")

        # 摘要（description）保留元数据描述
        desc = escape(post['description'])

        # 完整内容（content:encoded）使用正文 HTML，用 CDATA 包裹
        content_html = post['body_html']

        items_xml += f"""
    <item>
        <title>{escape(post['title'])}</title>
        <link>{link}</link>
        <description>{desc}</description>
        <content:encoded><![CDATA[{content_html}]]></content:encoded>
        <pubDate>{pub_date}</pubDate>
        <guid>{link}</guid>
    </item>"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
    <title>{escape(site_title)}</title>
    <link>{site_url}</link>
    <description>{escape(site_description)}</description>
    <language>zh-cn</language>
    {items_xml}
</channel>
</rss>"""

    feed_path = os.path.join(DIST_DIR, 'feed.xml')
    with open(feed_path, 'w', encoding='utf-8') as f:
        f.write(rss_xml)
    print(f"RSS feed 已生成（含全文，时间 UTC+8）：{feed_path}")

def build_all():
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
        
    posts_data = []
    # 递归遍历 posts 文件夹下的所有子文件夹
    for root, dirs, files in os.walk(POSTS_DIR):
        for file in files:
            if file.endswith('.md'):
                # 构造文件的完整路径供读取，例如 'posts/tech/python.md'
                full_path = os.path.join(root, file)
                print(f"正在处理: {full_path}")
                
                # 修改 process_single_post 使其接收完整路径
                data = process_single_post(full_path)
                if data:
                    posts_data.append(data)
    
    generate_index_and_tags(posts_data)
    generate_rss(posts_data, SITE_URL, SITE_TITLE, SITE_DESCRIPTION)
    print(f"\n构建完成! 共生成 {len(posts_data)} 篇文章，并已生成 feed.xml。")



if __name__ == "__main__":
    build_all()
