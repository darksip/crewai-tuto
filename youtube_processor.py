"""
Module de traitement YouTube - RSS feeds et résolution Channel IDs
"""

import subprocess
import feedparser
import json
import os
from datetime import datetime, timedelta

# Cache simple pour éviter de récupérer les IDs à chaque fois
CHANNEL_ID_CACHE_FILE = "channel_ids_cache.json"


def load_channel_id_cache():
    """Charger le cache des Channel IDs"""
    if os.path.exists(CHANNEL_ID_CACHE_FILE):
        try:
            with open(CHANNEL_ID_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_channel_id_cache(cache):
    """Sauvegarder le cache des Channel IDs"""
    try:
        with open(CHANNEL_ID_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde cache : {e}")

def extract_channel_name(url):
    """Extraire le nom de la chaîne depuis l'URL YouTube"""
    try:
        if "@" in url:
            # Format: https://www.youtube.com/@Underscore_
            return url.split("@")[-1]
        elif "/c/" in url:
            # Format: https://www.youtube.com/c/Micode
            return url.split("/c/")[-1]
        elif "/channel/" in url:
            # Format: https://www.youtube.com/channel/UCxxx
            return url.split("/channel/")[-1]
        else:
            # Fallback: prendre la dernière partie après /
            return url.split("/")[-1]
    except (IndexError, AttributeError):
        return url  # Retourner l'URL si extraction échoue


def get_channel_id_from_url(channel_url):
    """Obtenir l'ID de la chaîne depuis son URL YouTube avec cache"""
    # Charger le cache
    cache = load_channel_id_cache()
    
    # Vérifier si déjà en cache
    if channel_url in cache:
        print(f"📋 ID trouvé en cache pour {extract_channel_name(channel_url)}")
        return cache[channel_url]
    
    try:
        # Si c'est déjà un ID de chaîne
        if channel_url.startswith("UC") and len(channel_url) == 24:
            return channel_url

        # Si c'est une URL avec /channel/
        if "/channel/" in channel_url:
            channel_id = channel_url.split("/channel/")[-1].split("?")[0]
            # Sauvegarder en cache
            cache[channel_url] = channel_id
            save_channel_id_cache(cache)
            return channel_id

        # Utiliser la méthode curl/grep qui fonctionne parfaitement
        print(f"🔍 Recherche ID pour {extract_channel_name(channel_url)}...")
        cmd = f'''curl -sL "{channel_url}" | grep -oE '("channelId"|"externalId"|"ownerChannelId"):"UC[-_0-9A-Za-z]{{22}}' | head -n1 | grep -oE 'UC[-_0-9A-Za-z]{{22}}' '''

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            channel_id = result.stdout.strip()
            if channel_id.startswith("UC") and len(channel_id) == 24:
                # Sauvegarder en cache
                cache[channel_url] = channel_id
                save_channel_id_cache(cache)
                print(f"✅ ID trouvé et mis en cache : {channel_id}")
                return channel_id

        print(f"⚠️ Impossible de trouver l'ID pour {channel_url}")
        return None

    except Exception as e:
        print(f"❌ Erreur extraction ID chaîne {channel_url}: {e}")
        return None


def get_recent_videos_from_rss(channel_url, hours_limit=360):
    """Récupérer les vidéos récentes via RSS feed YouTube (15 jours par défaut)"""
    try:
        # Obtenir l'ID de la chaîne
        channel_id = get_channel_id_from_url(channel_url)
        if not channel_id:
            return []

        # Construire l'URL du flux RSS
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        # Parser le flux RSS
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"⚠️ Aucune vidéo trouvée dans le flux RSS pour {channel_url}")
            return []

        # Filtrer par date (dernières X heures)
        cutoff_time = datetime.now() - timedelta(hours=hours_limit)
        recent_videos = []

        for entry in feed.entries:
            try:
                # Parser la date de publication
                pub_date = datetime(*entry.published_parsed[:6])

                # Garder seulement les vidéos récentes
                if pub_date > cutoff_time:
                    video = {
                        "title": entry.title,
                        "url": entry.link,
                        "published": entry.published,
                        "channel": feed.feed.title
                        if hasattr(feed.feed, "title")
                        else extract_channel_name(channel_url),
                        "description": getattr(entry, "summary", ""),
                        "published_date": pub_date,
                    }
                    recent_videos.append(video)

            except Exception as e:
                print(f"⚠️ Erreur parsing vidéo : {e}")
                continue

        # Trier par date (plus récent en premier)
        recent_videos.sort(key=lambda x: x["published_date"], reverse=True)
        return recent_videos

    except Exception as e:
        print(f"❌ Erreur RSS pour {channel_url} : {e}")
        return []


def get_video_id_from_url(video_url):
    """Extraire l'ID de vidéo depuis une URL YouTube"""
    try:
        return video_url.split("watch?v=")[-1].split("&")[0]
    except (IndexError, AttributeError):
        return ""


def collect_videos_for_topic(topic, verbose=True):
    """Collecter toutes les vidéos YouTube pour un topic via RSS"""
    all_videos = []

    if verbose:
        print(f"📡 Récupération RSS pour {topic['name']} (15 derniers jours)...")

    for channel_url in topic["youtube_channels"]:
        channel_name = extract_channel_name(channel_url)

        if verbose:
            print(f"  📺 Analyse de {channel_name}...")

        videos = get_recent_videos_from_rss(channel_url, hours_limit=360)

        if videos:
            if verbose:
                print(f"    📊 {len(videos)} vidéo(s) trouvée(s) sur 15 jours")

            # Ajouter les métadonnées pour le traitement
            for video in videos:
                video["video_id"] = get_video_id_from_url(video["url"])
                video["channel_name"] = channel_name

            all_videos.extend(videos)
        else:
            if verbose:
                print("    ⚠️ Aucune vidéo trouvée")

    # Trier par date de publication (plus récent en premier)
    all_videos.sort(key=lambda x: x["published_date"], reverse=True)
    return all_videos


def test_rss_feeds(topics):
    """Tester les flux RSS pour tous les topics"""
    print("🧪 Test des flux RSS YouTube...")
    print("=" * 50)

    for topic in topics:
        print(f"\n📺 Topic : {topic['name']}")
        videos = collect_videos_for_topic(topic, verbose=True)

        if videos:
            print(f"✅ {len(videos)} vidéo(s) récente(s) :")
            for video in videos[:3]:  # Afficher les 3 premières
                print(f"  • {video['title']}")
                print(f"    Chaîne: {video['channel']} | Publié: {video['published']}")
                print(f"    URL: {video['url']}")
                print()
        else:
            print("⚠️ Aucune vidéo récente trouvée")
