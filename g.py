import sys
import os
import markdown
from datetime import datetime
from markdown.extensions.codehilite import CodeHiliteExtension
from collections import defaultdict

# 配置路径
POSTS_DIR = 'posts'
DIST_DIR = 'dist'

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
""" # 保持原样

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
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        dt_obj = datetime.now()

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
    print(f"\n构建完成! 共生成 {len(posts_data)} 篇文章。")



if __name__ == "__main__":
    # 如果传了参数则处理单个，否则扫描全量
    if len(sys.argv) == 2:
        # 单个文件处理模式
        # 注意：此处建议你也调用 build_all() 
        # 因为生成单篇后也需要刷新 index.html
        build_all() 
    else:
        build_all()
