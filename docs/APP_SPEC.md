# PlotWise – specyfikacja części E (aplikacja)

Dokument dla osoby lub agenta, który buduje aplikację webową. Opisuje, co ma powstać, z jakich plików korzysta i w jakiej kolejności to robić. Teksty interfejsu są po angielsku, bo użytkownikiem jest farmer z Kansas, a oceniają sędziowie NASA Space Apps.

## 1. Cel i terminy

PlotWise pozwala farmerowi z suchego rolnictwa (Tribune, hrabstwo Greeley, Kansas) „odtworzyć ostatnie 30 lat" na własnym polu przy różnych płodozmianach. Dla każdego płodozmianu pokazuje plon, zwrot netto, ryzyko złego roku i wpływ na glebę.

Historia, którą opowiada aplikacja: jeden farmer, jedno pole, jedno pytanie: „Co by było, gdybym przez ostatnie 30 lat prowadził to pole innym płodozmianem?"

| Termin | Co |
|---|---|
| sobota 14.11 | szkielet, Rotation replay, My field |
| niedziela 15.11, 14:00 | feature freeze |
| niedziela 15.11, 20:00 | wysyłka zgłoszenia |
| niedziela 15.11, 23:59 | twardy deadline |

## 2. Zanim napiszesz kod

1. Znajdź w repo prawdziwe pliki danych i przeczytaj ich klucze. Nie zakładaj struktury z tego dokumentu, tylko ją potwierdź:
   - `fields.geojson` (5 pól),
   - `climate/<field_id>.json`,
   - `results/<field_id>.json`,
   - `data/processed/ndvi/`,
   - `docs/img/` (podglądy NAIP, mapy ECOSTRESS, wykres walidacji),
   - `crops-economics/` (teksty kart, ceny, koszty; plan błędnie podaje `reference/`),
   - `evidence.md` (rozwinięcia identyfikatorów E01… i zdanie o ubezpieczeniach).
2. Nie buduj na `sample.json`. Różni się od prawdziwych plików: zaczyna od 1995 (prawdziwe od 1996), ma 4 płodozmiany zamiast 6, inne identyfikatory dowodów i mniej kluczy.
3. Jeśli czegoś z tej listy nie ma albo ma inną strukturę, zatrzymaj się i zgłoś to, zamiast zgadywać.

## 3. Stos technologiczny

- Vite + React + TypeScript, w nowym folderze `app/` w repo.
- Tailwind CSS + shadcn/ui. Komponenty można generować przez serwer MCP `21st` (nawigacja, karty, suwaki), ale kolory i typografia mają zostać takie jak w sekcji 4.
- Mapa: Leaflet przez `react-leaflet`.
- Wykresy: Recharts (używa go też shadcn/ui).
- Routing: `react-router` z `HashRouter`, żeby działało na GitHub Pages bez konfiguracji serwera.
- Bez backendu. Wszystkie dane to statyczne pliki JSON i obrazki.

Dane do aplikacji: skrypt `app/scripts/sync-data` kopiuje potrzebne pliki z repo do `app/public/data/` i `app/public/img/`. Uruchamiany przed `dev` i `build`. Nie edytujemy plików danych innych części.

Wdrożenie: GitHub Pages z `app/dist` przez GitHub Actions; w `vite.config` ustaw `base` na nazwę repo. Włączenie Pages wymaga właściciela repo.

## 4. Wygląd

Układ wzorowany na aplikacjach do monitoringu pól (lista pól po lewej, mapa w środku, karta pola po prawej). Styl własny.

| Rola | Kolor |
|---|---|
| tło strony | `#F4F5F1` |
| powierzchnie (karty) | `#FFFFFF` |
| tekst główny, górny pasek | `#16211B` |
| tekst pomocniczy | `#3A473F` |
| linie i obramowania | `#DDE1D9` |
| akcent główny, przyciski | `#1F5A3D` |
| dane na wykresach, zysk | `#1D5FA8` |
| strata / rok klęski | `#D08A5B` / `#5E1F0E` |
| tło ostrzeżenia | `#FBF3DC` z obramowaniem `#C9A23A` |

Kolory upraw, zawsze razem z literą w kafelku (nie polegamy na samym kolorze):

| Uprawa | Litera | Tło | Tekst |
|---|---|---|---|
| Wheat | W | `#E3B341` | `#16211B` |
| Sorghum | S | `#9A3F22` | `#FFFFFF` |
| Corn | C | `#2F7D5B` | `#FFFFFF` |
| Fallow | F | `#E4E1D6` | `#16211B` |

Typografia: Inter (tekst), Space Grotesk (nagłówki i duże liczby). Tekst podstawowy 15 px, najmniejszy 13 px (etykiety lat 11 px). Przyciski i suwaki mają co najmniej 44 px wysokości. Strona ma działać także na telefonie: kolumny się zawijają, szerokie wykresy przewijają się w poziomie.

## 5. Struktura aplikacji

Górny pasek na każdej stronie: logo PlotWise, cztery zakładki (My field, What has changed, Rotation replay, This season), wybrane pole (np. „Field 001 · W-S-F"), link „How we know".

Wybrane pole jest stanem globalnym (w adresie, np. `#/replay?field=001`). Domyślnie pole 001.

### 5.1 My field (`#/`)

Dane: `fields.geojson`, serie NDVI, obrazki z `docs/img/`.

- Lewa kolumna: lista 5 pól demo. Każde: identyfikator, płodozmian, jedno zdanie opisu.
- Środek: mapa Leaflet z granicami pól, wybrane pole wyróżnione. Przełącznik warstw: Aerial (NAIP), Greenness (NDVI), Surface heat (ECOSTRESS). Jeśli warstw rastrowych nie ma jako kafli, pokaż zwykły podkład i obrazki w karcie pola.
- Prawa kolumna, karta pola:
  - nazwa, hrabstwo, powierzchnia w akrach,
  - „Rotation today" jako kafelki liter,
  - „What grew here, 2008–2025": pasek 18 kafelków z historii upraw,
  - gleba i liczba dni z gołą ziemią,
  - wykres NDVI,
  - podglądy NAIP i ECOSTRESS,
  - przycisk „Replay the last 30 years on this field".
- Kliknięcie pola na liście lub na mapie zmienia wybrane pole.

Pięć pól ma prawie identyczne liczby w wynikach (dzielą pogodę i podobne gleby). Różnią się historią i obecnym płodozmianem, więc ten widok ma pokazywać właśnie historię.

### 5.2 What has changed (`#/changed`)

Dane: `climate/<field_id>.json` (12 trendów z etykietą „reliable").

- Nagłówek: „It is warmer here than when you started. Rain has not clearly changed."
- Cztery karty trendów, każda z liczbą na dekadę i małym wykresem 1994–2026:
  1. stopniodni wzrostu,
  2. pierwszy jesienny przymrozek (później),
  3. dni z ulewnym deszczem (więcej),
  4. ewapotranspiracja referencyjna (wyższa).
- Osobna, wyróżniona karta „Total rainfall: No reliable trend" z tekstem: NASA POWER pokazuje wysychanie, gridMET i PRISM tego nie potwierdzają, nie twierdzimy, że deszczu ubywa.
- GRACE: zmiana zapasu wody od 2002.
- Podsumowanie płodozmianów w hrabstwie (1221 pól) jako wykres słupkowy.
- ECOSTRESS: to samo popołudnie, ugór kontra sorgo.
- Pozostałych 8 trendów nie pokazujemy na głównym ekranie (ewentualnie rozwijana lista).

### 5.3 Rotation replay (`#/replay`), najważniejszy widok

Dane: `results/<field_id>.json` (6 płodozmianów: WF, WSF, WCF, WSSF, WWSF i opcjonalny WSfF; plony i zwrot netto 1996–2025; wyniki 0–1 w czterech kryteriach; teksty kart).

- Ostrzeżenie na górze, zawsze widoczne: „Read this as a comparison, not as farm profit. Every rotation shows a loss on average because we count full costs including land rent, and leave out crop insurance and program payments."
- Lewa kolumna: cztery suwaki 0–100 (Yield, Net return, Fewer bad years, Soil) i przycisk „Reset to equal weights".
- Środek: ranking płodozmianów. Każdy wiersz: miejsce, kafelki liter, nazwa, średni zwrot netto na akr, pasek dopasowania. Obecny płodozmian pola ma znacznik „Your rotation today".
- Ranking liczony w przeglądarce, bez uruchamiania silnika:

  ```
  fit = Σ (waga_k × wynik_k) / Σ waga_k      dla k w czterech kryteriach
  ```

  Gdy wszystkie wagi są zerowe, traktuj je jak równe.
- Pod rankingiem zdanie o stabilności: „It is a close call. Across random priorities, W-S-S-F comes out on top about 54% of the time and W-S-F about 41%. Your priorities decide."
- Prawa kolumna, karta wybranego płodozmianu. Sekcje w tej kolejności: Why, Evidence (identyfikatory E01… jako linki do „How we know"), What you gain, What we do not know, Check locally. Na dole każdej karty zdanie o ubezpieczeniach z `evidence.md`.
- Na dole wykres „Year by year": zwrot netto na akr dla wybranego płodozmianu w latach 1996–2025, z wyróżnionymi latami 2002, 2012 i 2013.

### 5.4 This season (`#/season`)

Dane: SMAP (wilgotność gleby 10.11.2026 w 96. percentylu dla tej daty).

- Duża liczba „96th percentile for this date" i skala od „Driest on record" do „Wettest on record" ze znacznikiem.
- Karta „What it means for next season" z uczciwym stanem: „We can show where the soil stands today. We cannot yet project the season from it." Silnik nie ma przebiegu w przód. Jeśli część D go dostarczy, w tym miejscu pojawi się prognoza.
- Nie dodawaj żadnych prognoz ani rad, których nie ma w danych.

### 5.5 How we know (`#/how`)

- Wykres walidacji z raportu silnika (obrazek z `docs/img/`).
- Cztery kafle: sorgo ok. 60% zmienności, pszenica ok. 45% (poza próbą dużo mniej), trafione lata klęsk 2002/2012/2013, kolejność ekonomiczna zgodna z badaniem K-State.
- Schemat fuzji danych: źródła → silnik → cztery widoki.
- Sekcja „What we do not claim": deszczu nie ubywa na pewno; liczby to nie zysk farmy; pięć pól demo niewiele się różni; pszenica jest modelowana słabo.
- Lista dowodów E01… rozwinięta z `evidence.md`.

## 6. Jednostki

Dane są metryczne, interfejs ma jednostki amerykańskie. Konwersje w jednym module, np. `app/src/lib/units.ts`:

| Z | Na | Przelicznik |
|---|---|---|
| kg/ha pszenicy | bu/acre | × 0,01487 (60 lb/bu) |
| kg/ha sorga lub kukurydzy | bu/acre | × 0,01593 (56 lb/bu) |
| mm | cale | ÷ 25,4 |
| cm | cale | ÷ 2,54 |
| °C | °F | × 1,8 + 32 |
| różnica lub suma stopni °C (np. stopniodni) | °F | × 1,8 |
| ha | akry | × 2,471 |
| USD/ha | USD/acre | ÷ 2,471 |

Przed konwersją sprawdź w pliku, w jakiej jednostce jest dana wartość. Zwroty netto mogą być już w USD/acre.

## 7. Pułapki w danych

- Pole 005 ma `current_rotation: null` z osobną notatką, bo nie pasuje do żadnego modelowanego płodozmianu. Interfejs ma to obsłużyć (np. „No fallow – not one of the modeled rotations") i nie pokazywać znacznika „Your rotation today".
- Zapis płodozmianu różni się między plikami: `W-S-F` w polach, `WSF` w wynikach. Zrób jedną funkcję normalizującą.
- `bare_days_per_year` występuje dwa razy z różnym znaczeniem: w polach to obserwacja z NDVI, w wynikach wartość modelowa dla płodozmianu. Podpisuj je różnie („seen from satellite" kontra „modeled").
- Lata w wynikach zaczynają się od 1996, pogoda od 1994, historia upraw od 2008.
- Identyfikatory E01… rozwijają się w `evidence.md`.

## 8. Zasady uczciwości przekazu

1. Zwrot netto zawsze jako porównanie między płodozmianami, nigdy jako zysk farmy.
2. Nigdzie nie pisz, że opadów ubywa.
3. Zwycięzca rankingu zależy od priorytetów; nie nazywaj żadnego płodozmianu „najlepszym" bez tego zastrzeżenia.
4. Brakujące dane pokazuj jako brak, nie wypełniaj ich wartościami przykładowymi.
5. Język prosty, bez żargonu: „greenness" zamiast samego „NDVI", „thirst of the air" obok „reference evapotranspiration".

## 9. Kolejność pracy

1. Szkielet: projekt w `app/`, nawigacja, pięć pustych tras, skrypt synchronizacji danych, wczytanie prawdziwych plików pola 001.
2. Rotation replay: suwaki, ranking, karta, wykres roczny.
3. My field: lista, mapa Leaflet, karta pola.
4. What has changed.
5. This season i How we know.
6. Konwersje jednostek wszędzie, obsługa pola 005, widok na telefonie.
7. Wdrożenie na GitHub Pages i sprawdzenie pod publicznym adresem.

Po każdym kroku: `npm run build` bez błędów, ręczne sprawdzenie w przeglądarce, potem zatrzymaj się.

**Git: agent tylko edytuje pliki.** Nie wykonuj `git add`, `git commit`, `git push`, `git pull` ani żadnej innej komendy zmieniającej historię lub gałęzie. Commity robi wyłącznie Miłosz. Po każdym kroku wypisz listę zmienionych plików i zaproponuj treść komunikatu commita, a z następnym krokiem poczekaj na jego potwierdzenie.

## 10. Poza zakresem aplikacji (reszta części E)

Nagranie demo, slajdy, tekst zgłoszenia, lista danych i źródeł, README, checklista w `docs/submission/`. Na dziś: przeczytać wymagania na zakładce Project (wymagane pola, format i limit długości demo).
