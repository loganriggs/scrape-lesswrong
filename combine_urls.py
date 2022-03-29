import os
import shutil

def combine_urls(url_dir = "urls_lesswrong"):
    url_filenames = sorted(os.listdir(url_dir), reverse=True)
    with open(url_dir+'/output_file.txt', 'wb') as output_file:
        latest_name = url_filenames[0]
        for f in url_filenames:
            with open(url_dir+"/"+f, 'rb') as fd:
                shutil.copyfileobj(fd, output_file)
            os.system(f'rm {url_dir}/{f}')
    os.system(f'mv {url_dir}/output_file.txt {url_dir}/{latest_name}')

combine_urls()