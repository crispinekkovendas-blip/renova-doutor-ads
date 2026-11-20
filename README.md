# Renova Doutor ads

Public since 2026-11-19, by the owner's choice: public repositories run on GitHub Actions for free, and the account's paid minutes were blocked. Everything here (photos, clips, texts, the doctor's name and CRM) is what the ads themselves show. Keep anything that must stay private out of this repository.

Builds the "one situation per ad" pictures and videos for the Renova Doutor telemedicine ads on GitHub Actions, so nothing has to run on the owner's PC. The people in the photos and clips are AI images (illustrative, not real patients).

## Pictures

- `build_micro.py`: the five situations, their texts and the layout (tag NÃO É SUS | CONSULTA PARTICULAR, the situation label, clinic, doctor, MÉDICO and CRM).
- `build_ads.py`: the doctor's data and the screenshot helper that the other programs import.
- `photos-native/`: the ten photos used.

Run **Build the Renova Doutor ads** from the Actions tab. The ten pictures, a contact sheet, a page with the texts (`micro.html`) and a list (`anuncios-micro.csv`) come out as the artifact `anuncios-micro`.

## Videos

One video per situation: a clip, the narrator, captions, and a closing card.

- `build_situacoes.py`: the five videos (which clip, which narration, the captions). It joins the narrator's three recordings (opening, standard ending, emergency line), times the captions from her pauses, and for clips whose faces sit where the captions go it moves the picture up (`up`) or blurs a strip at the bottom (`hide`), finding the cuts between shots by itself.
- `build_video.py` and `build_music.py`: the layout of a video (tag, captions, signature, closing card) and its soundtrack.
- `video-src/`: the clips and the narrator's recordings.

Run **Build the Renova Doutor videos** from the Actions tab, or:

```
gh workflow run build-videos.yml                  all five
gh workflow run build-videos.yml -f only="2 4"    only those situations
gh run download <run id> -n videos-situacoes -D <folder>
```

The videos (`video/`) and a sheet of frames for each (`sheets/`, one frame every 1.5 seconds) come out as the artifact `videos-situacoes`. The build log prints the second each caption appears, the cuts it found, and how far each picture was moved. The run's first step reads the programs for typing mistakes, so a broken program stops it in seconds.

## Where the originals are

The full project (all 100 photos, the earlier videos, the guides) stays on the owner's PC in `telemedicina-ads`. The programs there are the originals: change them there, copy them here, then run the workflow.
