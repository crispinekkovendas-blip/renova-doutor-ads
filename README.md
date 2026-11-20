# Renova Doutor ads

Public since 2026-11-19, by the owner's choice: public repositories run on GitHub Actions for free, and the account's paid minutes were blocked. Everything here (photos, texts, the doctor's name and CRM) is what the ads themselves show. Keep anything that must stay private out of this repository.

Builds the "one situation per ad" pictures for the Renova Doutor telemedicine ads on GitHub Actions, so nothing has to run on the owner's PC.

- `build_micro.py`: the five situations, their texts and the layout (tag NÃO É SUS | CONSULTA PARTICULAR, the situation label, clinic, doctor, MÉDICO and CRM).
- `build_ads.py`: the doctor's data and the screenshot helper that `build_micro.py` imports.
- `photos-native/`: the ten AI photos used (illustrative images, not real patients).

The videos, one per situation, are built here too:

- `build_situacoes.py`: the five videos (which clip, which narration, the captions); it times the captions from the narration.
- `build_video.py` and `build_music.py`: the layout of a video (tag, captions, signature, closing card) and its soundtrack.
- `video-src/`: the AI video clips and the narrator's recordings.

Run **Build the Renova Doutor videos** from the Actions tab; the videos and a sheet of frames for each come out as the artifact `videos-situacoes`.

For the pictures, run it from the Actions tab: **Build the Renova Doutor ads** > Run workflow. The pictures, a contact sheet, a page with the texts (`micro.html`) and a list (`anuncios-micro.csv`) come out as the artifact `anuncios-micro`.

The full project (all 100 photos, videos, guides) stays on the owner's PC in `telemedicina-ads`. Copy changes to `build_micro.py` or `build_ads.py` here before running.
