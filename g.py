import sys
import os
import markdown
import shutil
from datetime import datetime
from markdown.extensions.codehilite import CodeHiliteExtension
from pymdownx.arithmatex import ArithmatexExtension
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

# 注意：{prefix} 用于子目录页面回退到站点根目录（例如 "../"）
html_head = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iamzhz | {title}</title>
    <link rel="stylesheet" href="{prefix}styles.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.css" integrity="sha384-JctiRyLzXCrSoOOzFlSoWLdyzQl7OrrRnhyeBmzB6ZWtcjccUyc8lCQJqIbs3uQX" crossorigin="anonymous">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.js" integrity="sha384-+7Keh381hSkXmXqnjC0JBM/kzsN6TFj+wMKychSLjTvJ8/0ElMde2uKl8i6p6Buj" crossorigin="anonymous"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/contrib/auto-render.min.js" integrity="sha384-bjyGPfbij8/NDKJhSGZNP/khQVgtHUE5exjm4Ydllo42FwIgYsdLO2lXGmRBf5Mz" crossorigin="anonymous"
        onload="renderMathInElement(document.body);"></script>
    </head>
<body>
    <nav class="shiro-nav">
        <a href="{prefix}index.html" class="nav-brand">iamzhz<span>.</span></a>
        
        <div style="position: relative;">
            <ul class="nav-links" id="navLinks">
                <li><a href="{prefix}index.html" class="{index_cls}">首页</a></li>
                <li><a href="{prefix}tags.html" class="{tags_cls}">标签云</a></li>
                <li><a href="{prefix}about.html" class="{about_cls}">关于</a></li>
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


def render_page(title: str, body_html: str, prefix: str = "",
                active_index: bool = False,
                active_tags: bool = False,
                active_about: bool = False) -> str:
    """统一拼装页面，prefix 为回到 dist 根目录的相对路径（如 ''、'../'、'../../'）。"""
    head = html_head.format(
        title=title,
        prefix=prefix,
        index_cls="active" if active_index else "",
        tags_cls="active" if active_tags else "",
        about_cls="active" if active_about else "",
    )
    return head + body_html + html_tail


def rel_url_to_fs_path(rel_url: str) -> str:
    """把形如 'tech/python.html' 的相对 URL 转成当前系统下的文件路径。"""
    return os.path.join(DIST_DIR, *rel_url.split('/'))


def process_single_post(full_path: str):
    md = markdown.Markdown(extensions=[
        'tables', 'meta', 'fenced_code', 'toc',
        CodeHiliteExtension(linenums=True),
        ArithmatexExtension(generic=True),
    ])

    # 1. 读取内容
    content = get_file_content(full_path)
    if not content:
        return None
    body_html = md.convert(content)

    # 2. 计算输出路径：posts/tech/python.md -> tech/python.html
    rel_path = os.path.relpath(full_path, POSTS_DIR).replace(os.sep, '/')
    rel_dir = os.path.dirname(rel_path)                    # 'tech' 或 ''
    base_name = os.path.basename(rel_path)                 # 'python.md'
    file_slug = os.path.splitext(base_name)[0]             # 'python'

    output_rel = f"{rel_dir}/{file_slug}.html" if rel_dir else f"{file_slug}.html"
    output_path = rel_url_to_fs_path(output_rel)

    # 子目录页面需要 ../ 回退到 dist 根目录
    depth = len([p for p in rel_dir.split('/') if p]) if rel_dir else 0
    prefix = '../' * depth

    # 3. 提取元数据
    meta = getattr(md, 'Meta', {})
    title = meta.get('title', [None])[0]
    if not title:
        title = md.toc_tokens[0]['name'] if md.toc_tokens else file_slug

    date_str = meta.get('date', ['2026-01-01'])[0]
    try:
        dt_obj = parser.parse(date_str)
    except Exception:
        dt_obj = datetime(2026, 1, 1, 0, 0, 0)

    show_update_meta = meta.get('show-update', ['true'])[0].lower()
    show_update = show_update_meta in ('true', '1', 'yes', 'on')

    # 4. 生成 HTML
    full_html = render_page(
        title, body_html, prefix=prefix,
        active_index=False,
        active_about=(file_slug == 'about'),
    )

    # 5. 按原目录结构写入 dist
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return {
        'title': title,
        'date': dt_obj,
        'description': meta.get('description', ['暂无描述'])[0],
        'tags': meta.get('tags', []),
        'url': output_rel,          # 相对 dist 根目录的 URL，始终用 '/'
        'body_html': body_html,
        'show_update': show_update
    }


def generate_index_and_tags(all_posts):
    """汇总生成 index.html 和 tags.html（均在 dist 根目录，prefix 为空）"""

    # --- 1. 生成主页 (Index) ---
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
        f.write(render_page("首页", index_body, active_index=True))

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
        f.write(render_page("标签汇总", tags_body, active_tags=True))


def generate_rss(posts_data, site_url, site_title, site_description):
    """生成 RSS 2.0 格式的 feed.xml，包含全文内容，时间使用 UTC+8"""
    filtered_posts = [p for p in posts_data if p.get('show_update', True)]
    posts_sorted = sorted(filtered_posts, key=lambda x: x['date'], reverse=True)
    posts_sorted = posts_sorted[:RSS_MAX_ITEMS]
    items_xml = ""

    for post in posts_sorted:
        link = f"{site_url.rstrip('/')}/{post['url']}"

        # 发布时间使用北京时间（+0800）
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
            full_path = os.path.join(root, file)
            # 复制 SVG
            if file.lower().endswith('.svg'):
                rel_path = os.path.relpath(full_path, POSTS_DIR)
                dest_path = os.path.join(DIST_DIR, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(full_path, dest_path)
                print(f"已复制 SVG: {full_path} -> {dest_path}")
                continue
            # 处理 markdown
            if file.endswith('.md'):
                data = process_single_post(full_path)
                if data:
                    posts_data.append(data)
                print(f"已处理: {full_path}")

    generate_index_and_tags(posts_data)
    generate_rss(posts_data, SITE_URL, SITE_TITLE, SITE_DESCRIPTION)
    print(f"\n构建完成! 共生成 {len(posts_data)} 篇文章，并已生成 feed.xml。")


if __name__ == "__main__":
    build_all()
    shutil.copy2('styles.css', os.path.join(DIST_DIR, 'styles.css'))
