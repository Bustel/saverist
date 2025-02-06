# Saverist

Dieses Repository stellt den Versuch dar, Schnittmuster und andere Anleitungen von Makerist.de zu
sichern und ggf. besser nachnutzbar zu machen.

## Voraussetzungen

- Etwas Speicherplatz (etwa 1.5 GB pro 100 E-Books)
- Python 3 (getestet mit Python 3.12.5)
- Folgende Python-Bibliotheken werden benötigt:
  * `aiohttp`
  * `beautifulsoup4`

Diese können bspw. wie folgt installiert werden:

```
python3 -m pip install --user aiohttp beautifulsoup4
```

## Schnittmuster / E-Books herunterladen

```
python3 download_ebooks.py
```

## Was ist der andere Kram?

Das ist der Versuch, eine lokale Web-Applikation zu bauen, die das Archiv durchsuchbar darstellt.
Das ist noch sehr kaputt, also bitte ignorieren.
