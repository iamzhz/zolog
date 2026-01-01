import sys
import os
import markdown
from datetime import datetime
from markdown.extensions.codehilite import CodeHiliteExtension
from collections import defaultdict

# 配置路径
POSTS_DIR = 'posts'
DIST_DIR = 'dist'

html_head = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iamzhz | {}</title>
    <link rel="stylesheet" href="styles.css"></head>
<body>
    <div class="glow-cursor" id="glowCursor"></div>
    <nav class="shiro-nav">
        <a href="#" class="nav-brand">MyBlog<span>.</span></a>
        
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
""" # 省略重复部分，确保 .format(title) 能注入
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
""" # 保持原样

def get_file_content(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Cannot open file `{filename}`! Error: {e}")
        return ""

def process_single_post(filename: str):
    """处理单篇 Markdown，返回其元数据和生成的 HTML 文件名"""
    md = markdown.Markdown(extensions=[
        'tables', 'meta', 'fenced_code', 'toc',
        CodeHiliteExtension(linenums=True)
    ])
    
    content = get_file_content(os.path.join(POSTS_DIR, filename))
    if not content: return None

    body_html = md.convert(content)
    
    # 提取元数据
    meta = getattr(md, 'Meta', {})
    
    # 1. 标题逻辑：优先 meta > toc > 文件名
    title = meta.get('title', [None])[0]
    if not title:
        title = md.toc_tokens[0]['name'] if md.toc_tokens else filename.replace('.md', '')
    
    # 2. 日期逻辑：支持 2026 格式解析
    date_str = meta.get('date', ['2026-01-01'])[0]
    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        dt_obj = datetime.now() # 解析失败则用当前时间

    description = meta.get('description', ['暂无描述'])[0]
    tags = meta.get('tags', []) # 这是一个列表

    # 生成文章 HTML 页面
    output_filename = filename.replace('.md', '.html')
    format_args = ()
    if filename == 'about.md':
        format_args = (title, '', '', 'active')
    else:
        format_args = (title, 'active', '', '')
    full_html = html_head.format(*format_args) + body_html + html_tail
    
    with open(os.path.join(DIST_DIR, output_filename), 'w', encoding='utf-8') as f:
        f.write(full_html)

    return {
        'title': title,
        'date': dt_obj,
        'description': description,
        'tags': tags,
        'url': output_filename
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

def build_all():
    """扫描目录并执行构建"""
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
        
    posts_data = []
    for file in os.listdir(POSTS_DIR):
        if file.endswith('.md'):
            print(f"Processing {file}...")
            data = process_single_post(file)
            if data:
                posts_data.append(data)
    
    generate_index_and_tags(posts_data)
    print(f"\nDone! 总计生成 {len(posts_data)} 篇文章。")

if __name__ == "__main__":
    # 如果传了参数则处理单个，否则扫描全量
    if len(sys.argv) == 2:
        # 单个文件处理模式
        # 注意：此处建议你也调用 build_all() 
        # 因为生成单篇后也需要刷新 index.html
        build_all() 
    else:
        build_all()
