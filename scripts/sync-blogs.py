import requests
import argparse
import subprocess
import sys
import os
import json
import re

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

def get_image_file_basename(index):
    if index == 0:
        return 'cover'
    else:
        return 'image-{}'.format(index)

def get_image_file_ext(content_type):
    if content_type == 'image/png':
        return '.png'
    elif content_type == 'image/jpeg' or content_type == 'image/jpg':
        return '.jpg'
    else:
        raise RuntimeError('Unsupported image content type: {}'.format(content_type))

# Download images discovered in content, and replace with local names.
def download_images(content, directory):
    lines = []
    images = {}
    index = 0

    for line in content.splitlines():
        for match in re.finditer('!\[.*?\]\((.+?)\)', line):
            if match:
                url = match.group(1)
                if not url in images:
                    resp = requests.get(url)
                    ext = get_image_file_ext(resp.headers['Content-Type'])
                    basename = get_image_file_basename(index)
                    fn = basename + ext
                    images[url] = fn
                    index += 1

                    print('  Downloaded image {} as {}'.format(url, os.path.join(directory, fn)))

                    with open(os.path.join(directory, fn), 'wb') as f:
                        f.write(resp.content)

                filename = images[url]
                line = line.replace(url, filename)

        # cover image (index 0) must be the first image before any content.
        # if first non-empty content is not image, skip cover, it is a data issue.
        if line.strip() and index == 0:
            index += 1

        lines.append(line)

    return '\n'.join(lines)

def process_doc(doc_id):
    content = get_doc(doc_id)

    title = get_line_value(content, '^# (.+)$')
    slug = get_line_value(content, '^    slug: (.+)$')
    fm, body = extract_front_matter(content)

    md_path = os.path.join(git_root, 'content', 'blog', slug, 'index.md')
    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    body = download_images(body, os.path.dirname(md_path))

    with open(md_path, 'w') as f:
        f.write('---\n')
        f.write('title: "{}"\n'.format(title.replace('"', '\"')))
        f.write(fm)
        f.write('\n---\n')

        f.write(body)

def main():
    global access_token

    parser = argparse.ArgumentParser(description='Sync blog posts from Dropbox Paper.')
    parser.add_argument('--manifest', default='WKMNtdiJgFiILnlQJcLLG', help='The blog list doc.')
    parser.add_argument('--token', help='Dropbox access token')
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
        process_doc(doc_id)
        count += 1

    print('Successfully processed {} documents.'.format(count))

if __name__ == '__main__':
    main()
