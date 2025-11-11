import requests
import re

def is_download_link(url: str) -> bool:
    response = requests.head(url, allow_redirects=True, timeout=10)
    
    content_type = response.headers.get("Content-Type", "").lower()
    content_disposition = response.headers.get("Content-Disposition", "").lower()

    if "attachment" in content_disposition:
        return True

    if any(content_type.startswith(prefix) for prefix in [
        "application/",  # PDF, ZIP, DOCX, EXE и др.
        "image/",        # PNG, JPG и др.
        "audio/",        # MP3, WAV и др.
        "video/",        # MP4, AVI и др.
        "text/csv",      # CSV файлы
        "text/plain",    # TXT файлы
    ]):
        return True

    return False

def get_file_name(url: str) -> str | None:
    response = requests.head(url, allow_redirects=True, timeout=10)
    content_disposition = response.headers.get("Content-Disposition", "").lower().replace("\"", "").replace("\'", "")

    name_match_1 = re.search("(?<=filename=)[-.\w]+(?=;|$)", content_disposition)
    if (name_match_1):
        return name_match_1.group(0)
    
    name_match_2 = re.search("(?<=/)[-\w]+\.[\w]+(?=$|\?)", response.url)
    if (name_match_2):
        return name_match_2.group(0)
    
    return None


# print(get_file_name("https://github.com/maximakhmin/rag_search/archive/refs/heads/main.zip"))
# print(get_file_name("https://elar.urfu.ru/bitstream/10995/58606/1/978-5-7996-2357-9_2018.pdf?ysclid=mhrv68b9in427534228"))