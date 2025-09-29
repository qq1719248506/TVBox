coding=utf-8
import re
import json
import time
from urllib.parse import quote, urljoin, urlparse, parse_qs
import sys
# 导入外部库，现在可以正常使用
from bs4 import BeautifulSoup
import gzip
sys.path.append("..")
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        self.name = "好pb"
        self.hosts = {
            "main": "https://www.haopb.com",
            "backup": "https://haopb.com"
        }
        self.default_host = "main"
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # 视频格式支持
        self.VIDEO_FORMATS = ['.m3u8', '.mp4', '.flv', '.avi', '.mkv', '.mov']

    def getName(self):
        return self.name

    def init(self, extend=""):
        if extend:
            try:
                config = json.loads(extend)
                if config.get("host") in self.hosts:
                    self.default_host = config["host"]
                    self.log(f"已切换默认域名至：{self.hosts[self.default_host]}", "INFO")
            except:
                self.log("初始化参数解析失败，使用默认主域名", "WARNING")

    def log(self, msg, level="INFO"):
        print(f"[{level}] [{self.name}] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

    def get_current_host(self):
        return self.hosts[self.default_host]

    def homeContent(self, filter):
        result = {}
        result['class'] = [
            {"type_name": "电影", "type_id": "dianying", "land": "1", "filters": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": "dianying"},
                    {"n": "动作片", "v": "dongzuopian"},
                    {"n": "喜剧片", "v": "xijupian"},
                    {"n": "爱情片", "v": "aiqingpian"},
                    {"n": "科幻片", "v": "kehuanpian"},
                    {"n": "恐怖片", "v": "kongbupian"},
                    {"n": "剧情片", "v": "juqingpian"},
                    {"n": "战争片", "v": "zhanzhengpian"},
                    {"n": "动画片", "v": "donghuapian"},
                    {"n": "悬疑片", "v": "xuanyipian"},
                    {"n": "犯罪片", "v": "fanzuipian"},
                    {"n": "奇幻片", "v": "qihuanpian"},
                    {"n": "冒险片", "v": "maoxianpian"},
                    {"n": "纪录片", "v": "jilupian"}
                ]}
            ]},
            {"type_name": "电视剧", "type_id": "dianshiju", "land": "1", "filters": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": "dianshiju"},
                    {"n": "国产剧", "v": "guochanju"},
                    {"n": "港台剧", "v": "gangtaiju"},
                    {"n": "日韩剧", "v": "rihanju"},
                    {"n": "欧美剧", "v": "oumeiju"},
                    {"n": "海外剧", "v": "haiwaiju"}
                ]}
            ]},
            {"type_name": "综艺", "type_id": "zongyi", "land": "1", "filters": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": "zongyi"},
                    {"n": "内地综艺", "v": "neidizongyi"},
                    {"n": "港台综艺", "v": "gangtaizongyi"},
                    {"n": "日韩综艺", "v": "rihanzongyi"},
                    {"n": "欧美综艺", "v": "oumeizongyi"}
                ]}
            ]},
            {"type_name": "动漫", "type_id": "dongman", "land": "1", "filters": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": "dongman"},
                    {"n": "国产动漫", "v": "guochandongman"},
                    {"n": "日本动漫", "v": "ribendongman"},
                    {"n": "欧美动漫", "v": "oumeidongman"},
                    {"n": "海外动漫", "v": "haiwaidongman"}
                ]}
            ]}
        ]
        
        # 将所有筛选器数据添加进 result['filters'] 中
        result['filters'] = {
            "dianying": result['class'][0]['filters'],
            "dianshiju": result['class'][1]['filters'],
            "zongyi": result['class'][2]['filters'],
            "dongman": result['class'][3]['filters'],
        }

        return result

    def homeVideoContent(self):
        try:
            url = self.get_current_host()
            r = self.fetch(url, headers={"User-Agent": self.ua})
            
            if r.status_code != 200:
                self.log(f"首页推荐请求失败，状态码：{r.status_code}", "ERROR")
                return {'list': []}
            
            # 解析首页推荐内容
            soup = BeautifulSoup(r.text, 'html.parser')
            video_list = []
            
            # 查找首页的视频项
            items = soup.find_all('div', class_=['movie-item', 'video-item', 'item'])
            if not items:
                # 尝试其他可能的类名
                items = soup.find_all('li', class_=['movie-item', 'video-item', 'item'])
            
            for item in items[:12]:  # 限制12个结果
                try:
                    # 查找链接
                    link_tag = item.find('a')
                    if not link_tag or not link_tag.get('href'):
                        continue
                    
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = urljoin(self.get_current_host(), link)
                    
                    # 查找标题
                    title_tag = item.find(['h3', 'h4', 'p', 'span'], class_=['title', 'name'])
                    title = title_tag.text.strip() if title_tag else link_tag.get('title', '未知标题')
                    
                    # 查找图片
                    img_tag = item.find('img')
                    img_src = ""
                    if img_tag:
                        img_src = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-original', '')
                    
                    # 处理图片URL
                    if img_src.startswith('//'):
                        img_url = 'https:' + img_src
                    elif img_src and not img_src.startswith('http'):
                        img_url = urljoin(self.get_current_host(), img_src)
                    else:
                        img_url = img_src
                    
                    # 提取视频ID
                    vod_id = ""
                    if '/movie/' in link:
                        vod_id = link.split('/movie/')[-1].replace('/', '')
                    elif '/tv/' in link:
                        vod_id = link.split('/tv/')[-1].replace('/', '')
                    else:
                        # 从URL中提取ID
                        id_match = re.search(r'/(\d+)\.html', link)
                        if id_match:
                            vod_id = id_match.group(1)
                    
                    if not vod_id:
                        continue
                    
                    # 查找备注信息
                    remarks = []
                    remark_tags = item.find_all(['span', 'div'], class_=['tag', 'score', 'year', 'type'])
                    for tag in remark_tags:
                        remark_text = tag.text.strip()
                        if remark_text:
                            remarks.append(remark_text)
                    
                    vod_remarks = " / ".join(remarks[:2]) if remarks else "最新"
                    
                    vod = {
                        'vod_id': vod_id,
                        'vod_name': title,
                        'vod_pic': img_url,
                        'vod_remarks': vod_remarks
                    }
                    
                    video_list.append(vod)
                except Exception as e:
                    self.log(f"首页推荐项解析失败：{str(e)}", "ERROR")
                    continue
            
            self.log(f"首页推荐成功解析{len(video_list)}个项", "INFO")
            return {'list': video_list}
        except Exception as e:
            self.log(f"首页推荐内容获取失败：{str(e)}", "ERROR")
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        result = {'list': [], 'page': pg, 'pagecount': 1, 'limit': 40, 'total': 0}
        try:
            # 处理筛选参数
            filter_tid = tid
            if extend and 'class' in extend and extend['class']:
                filter_tid = extend['class']
            
            # 构建分类URL
            base_url = f"{self.get_current_host()}/{filter_tid}"
            if int(pg) > 1:
                url = f"{base_url}/page/{pg}"
            else:
                url = base_url
            
            r = self.fetch(url, headers={"User-Agent": self.ua})
            if r.status_code != 200:
                self.log(f"分类页请求失败，URL：{url}，状态码：{r.status_code}", "ERROR")
                return result
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 查找视频列表
            items = soup.find_all('div', class_=['movie-item', 'video-item', 'item'])
            if not items:
                items = soup.find_all('li', class_=['movie-item', 'video-item', 'item'])
            
            for item in items:
                try:
                    # 查找链接
                    link_tag = item.find('a')
                    if not link_tag or not link_tag.get('href'):
                        continue
                    
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = urljoin(self.get_current_host(), link)
                    
                    # 查找标题
                    title_tag = item.find(['h3', 'h4', 'p', 'span'], class_=['title', 'name'])
                    title = title_tag.text.strip() if title_tag else link_tag.get('title', '未知标题')
                    
                    # 查找图片
                    img_tag = item.find('img')
                    img_src = ""
                    if img_tag:
                        img_src = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-original', '')
                    
                    # 处理图片URL
                    if img_src.startswith('//'):
                        img_url = 'https:' + img_src
                    elif img_src and not img_src.startswith('http'):
                        img_url = urljoin(self.get_current_host(), img_src)
                    else:
                        img_url = img_src
                    
                    # 提取视频ID
                    vod_id = ""
                    if '/movie/' in link:
                        vod_id = link.split('/movie/')[-1].replace('/', '')
                    elif '/tv/' in link:
                        vod_id = link.split('/tv/')[-1].replace('/', '')
                    else:
                        id_match = re.search(r'/(\d+)\.html', link)
                        if id_match:
                            vod_id = id_match.group(1)
                    
                    if not vod_id:
                        continue
                    
                    # 查找备注信息
                    remarks = []
                    remark_tags = item.find_all(['span', 'div'], class_=['tag', 'score', 'year', 'type'])
                    for tag in remark_tags:
                        remark_text = tag.text.strip()
                        if remark_text:
                            remarks.append(remark_text)
                    
                    vod_remarks = " / ".join(remarks[:2]) if remarks else tid
                    
                    vod = {
                        'vod_id': vod_id,
                        'vod_name': title,
                        'vod_pic': img_url,
                        'vod_remarks': vod_remarks
                    }
                    
                    result['list'].append(vod)
                except Exception as e:
                    self.log(f"分类项解析失败：{str(e)}", "ERROR")
                    continue
            
            # 解析分页信息
            page_info = soup.find('div', class_=['pagination', 'page-nav'])
            if page_info:
                page_links = page_info.find_all('a')
                page_numbers = []
                for link in page_links:
                    page_text = link.text.strip()
                    if page_text.isdigit():
                        page_numbers.append(int(page_text))
                
                if page_numbers:
                    result['pagecount'] = max(page_numbers)
                else:
                    result['pagecount'] = int(pg)
            else:
                result['pagecount'] = int(pg)

            self.log(f"分类{tid}第{pg}页：解析{len(result['list'])}项", "INFO")
            return result
        except Exception as e:
            self.log(f"分类内容获取失败：{str(e)}", "ERROR")
            return result

    def detailContent(self, ids):
        result = {"list": []}
        if not ids:
            return result
        
        vod_id = ids[0]
        try:
            # 尝试不同的详情页URL格式
            detail_urls = [
                f"{self.get_current_host()}/movie/{vod_id}",
                f"{self.get_current_host()}/tv/{vod_id}",
                f"{self.get_current_host()}/detail/{vod_id}",
                f"{self.get_current_host()}/{vod_id}.html"
            ]
            
            detail_url = None
            r = None
            
            for url in detail_urls:
                r = self.fetch(url, headers={"User-Agent": self.ua})
                if r.status_code == 200:
                    detail_url = url
                    break
            
            if not detail_url:
                self.log(f"详情页请求失败，ID：{vod_id}", "ERROR")
                return result
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 提取标题
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.text.strip() if title_tag else "未知标题"
            title = title.replace(" - 好平部", "").replace(" - 好平部影视", "").strip()
            
            # 提取封面图
            cover_url = ""
            cover_tag = soup.find('img', class_=['poster', 'cover', 'thumb'])
            if cover_tag:
                cover_src = cover_tag.get('src') or cover_tag.get('data-src') or cover_tag.get('data-original', '')
                if cover_src:
                    if cover_src.startswith('//'):
                        cover_url = 'https:' + cover_src
                    elif not cover_src.startswith('http'):
                        cover_url = urljoin(self.get_current_host(), cover_src)
                    else:
                        cover_url = cover_src
            
            # 提取描述
            desc = ""
            desc_tag = soup.find('div', class_=['description', 'desc', 'intro', 'summary'])
            if desc_tag:
                desc = desc_tag.text.strip()
            
            # 提取播放信息
            play_sources = []
            play_urls = []
            
            # 查找播放器容器
            player_container = soup.find('div', id=['player', 'playlist', 'video-player'])
            if not player_container:
                player_container = soup.find('div', class_=['player', 'playlist', 'video-container'])
            
            if player_container:
                # 查找播放线路
                source_tabs = player_container.find_all(['li', 'div'], class_=['tab', 'source-tab'])
                if source_tabs:
                    for tab in source_tabs:
                        source_name = tab.text.strip()
                        if source_name and source_name not in play_sources:
                            play_sources.append(source_name)
                
                # 如果没找到线路标签，尝试查找视频iframe
                if not play_sources:
                    iframe = player_container.find('iframe')
                    if iframe and iframe.get('src'):
                        play_sources = ["默认线路"]
                        play_urls = [f"正片${iframe['src']}"]
            
            # 如果没有找到播放信息，尝试从JavaScript中提取
            if not play_sources:
                script_pattern = r'var\s+(player_|video_|play_|url)\s*=\s*[\'"]([^\'"]+)[\'"]'
                script_matches = re.findall(script_pattern, r.text)
                for match in script_matches:
                    if len(match) > 1 and any(fmt in match[1] for fmt in self.VIDEO_FORMATS):
                        play_sources = ["默认线路"]
                        play_urls = [f"正片${match[1]}"]
                        break
            
            # 如果还是没找到，尝试通用的视频URL匹配
            if not play_sources:
                video_pattern = r'["\'](https?://[^"\']*\.(?:m3u8|mp4|flv)[^"\']*)["\']'
                video_matches = re.findall(video_pattern, r.text)
                if video_matches:
                    play_sources = ["默认线路"]
                    episodes = []
                    for idx, url in enumerate(video_matches[:10]):  # 限制前10个
                        episodes.append(f"第{idx+1}集${url}")
                    play_urls = ["#".join(episodes)]
            
            vod = {
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": cover_url,
                "vod_content": desc,
                "vod_play_from": "$$$".join(play_sources) if play_sources else "默认线路",
                "vod_play_url": "$$$".join(play_urls) if play_urls else "正片$"
            }
            
            result["list"].append(vod)
            self.log(f"详情页解析成功，ID：{vod_id}", "INFO")
            return result
        except Exception as e:
            self.log(f"详情页解析失败，ID：{vod_id}，错误：{str(e)}", "ERROR")
            return result

    def playerContent(self, flag, id, vipFlags):
        try:
            # 如果id已经是URL，直接返回
            if id.startswith('http'):
                return {
                    "parse": 0,
                    "playUrl": '',
                    "url": id,
                    "header": {
                        "User-Agent": self.ua,
                        "Referer": self.get_current_host() + "/"
                    }
                }
            
            # 这是一个简单的播放器URL解析
            return {
                "parse": 0,
                "playUrl": '',
                "url": id,
                "header": {
                    "User-Agent": self.ua,
                    "Referer": self.get_current_host() + "/"
                }
            }
        except Exception as e:
            self.log(f"播放地址解析失败：{str(e)}", "ERROR")
            return {"parse": 0, "playUrl": '', "url": id, "header": {"User-Agent": self.ua}}

    def searchContent(self, key, quick):
        result = {"list": []}
        try:
            # 构造搜索URL
            search_url = f"{self.get_current_host()}/search/{quote(key)}"
            r = self.fetch(search_url, headers={"User-Agent": self.ua})
            
            if r.status_code != 200:
                self.log(f"搜索请求失败，状态码：{r.status_code}", "ERROR")
                return result
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 查找搜索结果
            items = soup.find_all('div', class_=['movie-item', 'video-item', 'item'])
            if not items:
                items = soup.find_all('li', class_=['movie-item', 'video-item', 'item'])
            
            for item in items:
                try:
                    # 查找链接
                    link_tag = item.find('a')
                    if not link_tag or not link_tag.get('href'):
                        continue
                    
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = urljoin(self.get_current_host(), link)
                    
                    # 查找标题
                    title_tag = item.find(['h3', 'h4', 'p', 'span'], class_=['title', 'name'])
                    title = title_tag.text.strip() if title_tag else link_tag.get('title', '未知标题')
                    
                    # 检查标题是否包含搜索关键词
                    if key.lower() not in title.lower():
                        continue
                    
                    # 查找图片
                    img_tag = item.find('img')
                    img_src = ""
                    if img_tag:
                        img_src = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-original', '')
                    
                    # 处理图片URL
                    if img_src.startswith('//'):
                        img_url = 'https:' + img_src
                    elif img_src and not img_src.startswith('http'):
                        img_url = urljoin(self.get_current_host(), img_src)
                    else:
                        img_url = img_src
                    
                    # 提取视频ID
                    vod_id = ""
                    if '/movie/' in link:
                        vod_id = link.split('/movie/')[-1].replace('/', '')
                    elif '/tv/' in link:
                        vod_id = link.split('/tv/')[-1].replace('/', '')
                    else:
                        id_match = re.search(r'/(\d+)\.html', link)
                        if id_match:
                            vod_id = id_match.group(1)
                    
                    if not vod_id:
                        continue
                    
                    vod = {
                        "vod_id": vod_id,
                        "vod_name": title,
                        "vod_pic": img_url,
                        "vod_remarks": "搜索结果"
                    }
                    
                    result["list"].append(vod)
                except Exception as e:
                    self.log(f"搜索项解析失败：{str(e)}", "ERROR")
                    continue
            
            self.log(f"搜索成功解析{len(result['list'])}个项", "INFO")
            return result
        except Exception as e:
            self.log(f"搜索内容获取失败：{str(e)}", "ERROR")
            return result

    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        return any(url.lower().endswith(fmt) for fmt in self.VIDEO_FORMATS)

    def manualVideoCheck(self):
        pass

    def localProxy(self, param):
        pass