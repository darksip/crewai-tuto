"""
Gestionnaire de persistence quotidienne - Organisation par date de publication
"""
import json
from datetime import datetime
from pathlib import Path
from youtube_processor import get_video_id_from_url


def create_daily_directory(date):
    """Créer le répertoire daily pour une date donnée"""
    date_str = date.strftime("%Y-%m-%d")
    daily_dir = Path("daily") / date_str
    daily_dir.mkdir(parents=True, exist_ok=True)
    return daily_dir


def get_processed_videos(daily_dir):
    """Récupérer la liste des vidéos déjà traitées pour une date"""
    processed_file = daily_dir / "videos_processed.json"

    if processed_file.exists():
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("video_ids", []))
        except Exception as e:
            print(f"⚠️ Erreur lecture videos_processed.json : {e}")

    return set()


def save_processed_video(daily_dir, video):
    """Sauvegarder une vidéo comme traitée dans son répertoire daily"""
    processed_file = daily_dir / "videos_processed.json"

    # Charger les vidéos déjà traitées
    processed_data = {"video_ids": [], "videos": []}
    if processed_file.exists():
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_data = json.load(f)
        except Exception:
            pass

    # Ajouter la nouvelle vidéo si pas déjà présente
    video_id = get_video_id_from_url(video["url"])

    if video_id not in processed_data["video_ids"]:
        processed_data["video_ids"].append(video_id)
        processed_data["videos"].append(
            {
                "video_id": video_id,
                "title": video["title"],
                "url": video["url"],
                "channel": video["channel"],
                "published": video["published"],
                "processed_at": datetime.now().isoformat(),
            }
        )

        # Sauvegarder
        try:
            with open(processed_file, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur sauvegarde video processée : {e}")


def filter_new_videos(videos, verbose=True):
    """Filtrer les vidéos pour ne garder que les non-traitées"""
    new_videos = []
    new_videos_count = 0

    for video in videos:
        pub_date = video["published_date"].date()
        daily_dir = create_daily_directory(pub_date)

        # Vérifier si déjà traitée
        processed_videos = get_processed_videos(daily_dir)
        video_id = get_video_id_from_url(video["url"])

        if video_id not in processed_videos:
            video["daily_dir"] = daily_dir
            video["video_id"] = video_id
            new_videos.append(video)
            new_videos_count += 1
            
            if verbose:
                print(f"    🆕 Nouvelle vidéo pour {pub_date}: {video['title'][:50]}...")
        else:
            if verbose:
                print(f"    ⏭️  Déjà traitée ({pub_date}): {video['title'][:50]}...")

    if verbose:
        print(f"📈 Total : {new_videos_count} nouvelles vidéos à traiter")

    return new_videos


def group_videos_by_date(videos):
    """Grouper les vidéos par date de publication"""
    videos_by_date = {}
    
    for video in videos:
        pub_date = video["published_date"].date()
        if pub_date not in videos_by_date:
            videos_by_date[pub_date] = []
        videos_by_date[pub_date].append(video)
    
    return videos_by_date


def save_synthesis_by_date(synthesis_content, topic_name, pub_date):
    """Sauvegarder une synthèse dans le répertoire daily de sa date"""
    daily_dir = create_daily_directory(pub_date)
    synthesis_file = daily_dir / f"synthese_{topic_name.replace(' ', '_')}_{pub_date}.md"
    
    try:
        with open(synthesis_file, "w", encoding="utf-8") as f:
            f.write(synthesis_content)
        
        print(f"✅ Synthèse {pub_date} sauvée : {synthesis_file}")
        return str(synthesis_file)
    except Exception as e:
        print(f"❌ Erreur sauvegarde synthèse {pub_date} : {e}")
        return None


def mark_videos_as_processed(date_videos):
    """Marquer toutes les vidéos d'une date comme traitées"""
    for video in date_videos:
        save_processed_video(video["daily_dir"], video)


def get_daily_status():
    """Obtenir le statut de tous les répertoires daily"""
    daily_base = Path("daily")
    
    if not daily_base.exists():
        return {"error": "Aucun répertoire daily trouvé"}

    # Parcourir les répertoires de dates
    date_dirs = sorted(
        [d for d in daily_base.iterdir() if d.is_dir()], reverse=True
    )

    if not date_dirs:
        return {"error": "Aucun répertoire de date trouvé"}

    daily_stats = {}
    
    for date_dir in date_dirs[:10]:  # 10 derniers jours
        date_name = date_dir.name
        
        # Compter les vidéos traitées
        processed_file = date_dir / "videos_processed.json"
        video_count = 0
        videos_details = []
        
        if processed_file.exists():
            try:
                with open(processed_file, "r") as f:
                    data = json.load(f)
                    video_count = len(data.get("video_ids", []))
                    videos_details = data.get("videos", [])
            except Exception:
                pass

        # Compter les synthèses
        synthesis_files = list(date_dir.glob("synthese_*.md"))

        daily_stats[date_name] = {
            "videos_count": video_count,
            "videos_details": videos_details,
            "synthesis_count": len(synthesis_files),
            "synthesis_files": [f.name for f in synthesis_files]
        }

    return daily_stats


def display_daily_status():
    """Afficher le statut des répertoires daily"""
    print("📊 Statut des répertoires daily...")
    print("=" * 50)

    stats = get_daily_status()
    
    if "error" in stats:
        print(f"⚠️ {stats['error']}")
        return

    for date_name, date_stats in stats.items():
        print(f"\n📅 {date_name}")
        print(f"  📹 Vidéos traitées : {date_stats['videos_count']}")
        print(f"  📝 Synthèses : {date_stats['synthesis_count']}")

        if date_stats['synthesis_files']:
            for synth_file in date_stats['synthesis_files']:
                print(f"    • {synth_file}")