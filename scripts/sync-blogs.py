import requests
import argparse
import subprocess
import sys
import os
import json
import re
from PIL import Image
from io import BytesIO

if sys.version_info.major < 3 or sys.version_info.minor < 7:
    print('Python 3.7+ is required.')
    sys.exit(1)

try:
    global git_root
    git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    print('Using root directory: {}'.format(git_root))
except:
    print('Git not found or not in a Git repository.')
    sys.exit(1)

access_token = os.environ.get('VIBE_CMS_TOKEN', '')

def get_doc(doc_id):
    arg = {'doc_id': doc_id, 'export_format': { '.tag': 'markdown' }}
    resp = requests.post('https://api.dropboxapi.com/2/paper/docs/download',
            headers={'authorization': 'Bearer {}'.format(access_token), 'Dropbox-API-Arg': json.dumps(arg) },
            )

    if resp.status_code != 200:
        raise RuntimeError('Failed to download doc id: {}'.format(doc_id))

    return resp.content.decode('utf-8')

def parse_doc_list(content):
    for line in content.splitlines():
        m = re.search('\(https://paper\.dropbox\.com/doc/([^/]+?)-(\w+)\)', line)
        if m:
            # [doc_id, doc_name]
            yield [m.group(2), m.group(1)]

def get_line_value(content, pattern, group_id = 1):
    for line in content.splitlines():
        m = re.search(pattern, line)
        if m:
            return m.group(group_id)

def extract_front_matter(content):
    inFM = False
    inBody = False
    fm = []
    body = []

    for line in content.splitlines():
        if inBody:
            body.append(line)
        elif line.strip() == '---':
            if inFM:
                inFM = False
                inBody = True
            else:
                inFM = True
        elif inFM:
            fm.append(line[4:])

    return '\n'.join(fm), '\n'.join(body)

def get_image_file_ext(content_type):
    if content_type == 'image/png':
        return '.png'
    elif content_type == 'image/jpeg' or content_type == 'image/jpg':
        return '.jpg'
    else:
        raise RuntimeError('Unsupported image content type: {}'.format(content_type))

# Download images discovered in content, and replace with hugo shortcode local names.
def download_images(content, directory):
    lines = []
    images = {}
    index = 0
    has_cover = False
    has_content = False

    for line in content.splitlines():
        any_match = False
        for match in re.finditer('!\[(.*?)\]\((.+?)\)', line):
            any_match = True
            if match:
                caption = match.group(1)
                url = match.group(2)
                if not url in images:
                    resp = requests.get(url)
                    ext = get_image_file_ext(resp.headers['Content-Type'])
                    basename = 'image-{}'.format(index) if has_content else 'cover'
                    if basename == 'cover':
                        with Image.open(BytesIO(resp.content)) as img:
                            width, height = img.size
                            if width / height > 1.95:
                                basename = 'cover-fullwidth'

                    # only accept one cover image per blog post.
                    if basename == 'cover' and has_cover:
                        print('  WARNING: ignored additional cover image: {}'.format(url))
                        line = ''
                        continue

                    fn = basename + ext
                    images[url] = fn
                    index += 1

                    with open(os.path.join(directory, fn), 'wb') as f:
                        f.write(resp.content)

                    print('  Downloaded image {} as {}'.format(url, os.path.join(directory, fn)))

                # do not put cover-fullwidth into md file
                if basename == 'cover-fullwidth':
                    line = ''
                else:
                    filename = images[url]
                    line = line.replace(match.group(0), '{{{{< common/srcset "{}" "{}" >}}}}'.format(filename, caption))

                    if basename == 'cover':
                        has_cover = True

                        # new blog style does not need cover in md file
                        line = ''

        if not any_match and line.strip():
            has_content = True

        lines.append(line)

    return '\n'.join(lines)

def process_doc(doc_id, is_dev):
    content = get_doc(doc_id)

    title = get_line_value(content, '^# (.+)$')
    slug = get_line_value(content, '^    slug: (.+)$')
    fm, body = extract_front_matter(content)

    if is_dev:
        slug = 'dev-' + slug
        fm = fm.replace('slug: ', 'slug: dev-')

    md_path = os.path.join(git_root, 'content', 'blog', slug, 'index.md')
    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    body = download_images(body, os.path.dirname(md_path))

    with open(md_path, 'w') as f:
        f.write('---\n')
        f.write('title: "{}"\n'.format(title.replace('"', '\"')))
        f.write(fm)
        if is_dev:
            f.write('\nexpiryDate: 2018-01-01 # This makes post only show in dev environment\n')
        f.write('\n---\n')

        f.write(body)
        if not body.endswith('\n'):
            f.write('\n')

def main():
    global access_token

    parser = argparse.ArgumentParser(description='Sync blog posts from Dropbox Paper.')
    parser.add_argument('--manifest', default='XWvIYMXhbzTYauPlxCd7j', help='The blog list doc.')
    parser.add_argument('--token', help='Dropbox access token')
    parser.add_argument('--dev', action='store_true', help='download as dev post')
    args = parser.parse_args()

    if args.token:
        access_token = args.token

    if not access_token:
        print('VIBE_CMS_TOKEN is required');
        sys.exit(1)

    manifest_content = get_doc(args.manifest)
    count = 0
    for doc in parse_doc_list(manifest_content):
        doc_id = doc[0]
        doc_name = doc[1]
        print('Processing doc {}: {}'.format(doc_id, doc_name))
        process_doc(doc_id, args.dev)
        count += 1

    print('Successfully processed {} documents.'.format(count))

if __name__ == '__main__':
    main()
