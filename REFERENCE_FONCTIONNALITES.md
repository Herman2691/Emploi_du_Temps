# UniSchedule — Référence complète des fonctionnalités

> Document de référence pour la migration Laravel/Hostinger.
> Généré le 2026-05-17 depuis le code source de l'application Streamlit.

---

## Table des matières

1. [Espace Public (visiteur)](#1-espace-public-visiteur)
2. [Espace Étudiant](#2-espace-étudiant)
3. [Espace Professeur](#3-espace-professeur)
4. [Administration — Admin Département](#4-administration--admin-département)
5. [Administration — Admin Faculté](#5-administration--admin-faculté)
6. [Administration — Admin Université](#6-administration--admin-université)
7. [Administration — Super Admin](#7-administration--super-admin)
8. [Modèle de données (résumé)](#8-modèle-de-données-résumé)

---

## 1. Espace Public (visiteur)

### Page Accueil (`pages/1_Accueil.py`)
- Affichage du nom de l'application, logo, description
- Liens vers les espaces (étudiant, professeur, administration)
- Affichage des communiqués publics (annonces)
- Sélecteur d'université → faculté → département pour accéder à l'emploi du temps public

### Page Emploi du Temps (`pages/2_Horaire.py`)
- Filtres : université → faculté → département → promotion → option → année académique → session
- Vue grille hebdomadaire (lundi–samedi, 07h00–21h00, créneaux de 1h30)
- Affichage des cours : matière, salle, professeur, type (CM/TD/TP)
- Téléchargement PDF de l'emploi du temps (FPDF2)
- Export iCal (.ics) pour Google Calendar / Outlook
- Génération QR Code de l'emploi du temps (image PNG)
- Pas d'authentification requise

---

## 2. Espace Étudiant

### Connexion (`pages/10_Student_Auth.py`)
- Formulaire : numéro étudiant + mot de passe
- Mot de passe par défaut = numéro étudiant
- Session stockée dans `st.session_state` (`current_student`)
- Bouton déconnexion dans la sidebar

### Tableau de bord étudiant (`pages/11_Student_Dashboard.py`)

#### Onglet Mon Emploi du Temps
- Vue grille de l'emploi du temps de sa promotion/option
- Filtres : semaine, session
- Bouton téléchargement PDF de son emploi du temps
- Bouton export iCal (.ics)

#### Onglet Mes TPs / Travaux
- Liste des travaux pratiques assignés à sa promotion
- Détails : matière, description, date limite, professeur

#### Onglet Mes Notes
- Notes par UE / EC (Unité d'Enseignement / Élément Constitutif)
- Calcul des moyennes pondérées par session
- Statut : admis / ajourné / rattrapage

#### Onglet Mon Programme
- Programme des cours de sa promotion par session (Session 1, Session 2…)
- Groupé par UE avec ses ECs

#### Onglet Mon Bulletin
- Bulletin de notes avec en-tête université/faculté/département
- Téléchargement PDF (FPDF2)
- Informations : rang, crédits obtenus, mention

#### Onglet Assiduité
- Liste des présences/absences par cours
- Pointage par code QR : l'étudiant saisit le code à 6 caractères généré par le professeur
- Statistiques : taux de présence, nombre d'absences justifiées/non justifiées

#### Onglet Messagerie
- **Messages reçus** : liste des réponses de l'administration, statut lu/non lu
- **Contacter l'administration** : formulaire (sujet + message), envoi vers l'admin département

#### Onglet Parcours / Progression
- Années académiques suivies
- Crédits validés par année
- Statut d'avancement (1ère année, 2ème année, etc.)

#### Onglet Frais de Scolarité
- Détail des frais par catégorie (inscription, scolarité, examens…)
- Montants payés vs montants dus
- Statut de paiement

#### Onglet Mes Fiches
- Fiche d'inscription PDF (FPDF2) avec données personnelles et académiques
- Fiche de résultats PDF

#### Onglet Mon Profil
- Informations personnelles (nom, prénom, numéro étudiant, promotion)
- Changement de mot de passe

---

## 3. Espace Professeur

### Connexion (`pages/12_Prof_Auth.py`)
- Formulaire : email + mot de passe
- Authentification via table `users` (role = "professeur")
- Session stockée dans `st.session_state` (`current_user`)

### Tableau de bord professeur (`pages/9_Prof_Dashboard.py`)

#### Onglet Mon Horaire
- Vue grille de ses cours de la semaine
- Filtres : semaine, département
- Affichage : matière, salle, promotion, type de cours

#### Onglet Documents / Ressources
- Upload de documents pour ses étudiants (PDF, Word, etc.)
- Liste des documents partagés avec une promotion

#### Onglet TPs / Travaux Pratiques
- Création de travaux (titre, description, date limite, promotion ciblée)
- Modification et suppression de ses travaux
- Suivi des remises (si activé)

#### Onglet Notes
- Saisie des notes par EC (Élément Constitutif) et par étudiant
- Import Excel de notes (colonnes : numéro étudiant, note)
- Calcul automatique des moyennes
- Visualisation des notes saisies

#### Onglet Mes Classes
- Liste des promotions/options dont il est responsable ou rattaché
- Informations : faculté, département, effectif

#### Onglet Présences / Assiduité
- Liste des ses créneaux de cours
- Génération d'un code QR de présence pour un créneau donné
  - Code valable 45 minutes
  - Affichage QR image + code textuel à 6 caractères
  - Désactivation automatique du code précédent lors d'une nouvelle génération
- Marquage manuel de présences/absences étudiant par étudiant
- Historique des présences par cours

#### Onglet Messages
- Réception des messages entrants (admin, étudiants si activé)
- Envoi de messages à l'administration

#### Onglet Réclamations
- Soumission de réclamations à l'administration du département
- Suivi du statut (en attente, traité)

---

## 4. Administration — Admin Département

> Rôle : `admin_departement`
> Accès à tout ce qui concerne son département.
> Dashboard : `pages/8_Admin_Dashboard.py` — fonction `render_admin_departement()`

### Onglet 1 — Promotions
- Liste des promotions du département
- Ajout / modification / suppression d'une promotion
- Champs : nom, niveau (L1–M2), année académique

### Onglet 2 — Filières
- Liste des filières rattachées au département
- Ajout / modification / suppression d'une filière

### Onglet 3 — Options
- Liste des options par filière
- Ajout / modification / suppression d'une option

### Onglet 4 — Cours / Programme (UE & EC)
- Liste des Unités d'Enseignement (UE) par promotion et session
- Ajout / modification / suppression d'une UE
  - Champs : code, libellé, crédits ECTS, session (Session 1, 2, 3…), coefficient
- Ajout / modification / suppression d'un EC (Élément Constitutif) dans une UE
  - Champs : code, libellé, type (CM/TD/TP), crédits, coefficient, professeur responsable
- Renommage sessions : A/B/C en base → Session 1/2/3 à l'affichage (sans changement de schéma)

### Onglet 5 — Professeurs
- Liste des professeurs rattachés au département
- Ajout d'un rattachement professeur–département
- Retrait d'un rattachement

### Onglet 6 — Emploi du Temps
- Grille de l'emploi du temps du département
- Ajout d'un cours (EC) au planning
  - Champs : EC, salle, jour, heure début/fin, type, session, promotion, professeur
  - Sélecteur de session (Session 1 / Session 2…)
- Modification / suppression d'un créneau
- Vérification de conflits de salle et de professeur

### Onglet 7 — Salles
- Liste des salles disponibles
- Ajout / modification / suppression d'une salle
- Champs : nom, capacité, type (amphi, salle TP, salle TD)

### Onglet 8 — Notes
- Saisie / modification des notes par étudiant, EC, et session
- Import Excel des notes (colonnes : numéro étudiant, note)
- Calcul et affichage des moyennes

### Onglet 9 — Registre Étudiants
- Liste des étudiants du département
- Ajout manuel d'un étudiant
- **Import Excel** d'une liste d'étudiants
  - Colonnes attendues : numéro étudiant, nom, prénom, promotion, année académique, sexe, provenance
  - Détection des doublons par numéro étudiant + université
- Modification des informations d'un étudiant
- Réinitialisation du mot de passe (champ vide → reset au numéro étudiant)
- Suppression d'un étudiant
- **Messagerie étudiants** : liste des messages entrants depuis les étudiants, possibilité de répondre

### Onglet 10 — Présences
- Tableau de présence par cours et par étudiant
- Filtres : promotion, EC, date
- Export CSV des présences

### Onglet 11 — Résultats
- Tableau des résultats par promotion et session
- Calcul automatique : moyenne générale, crédits obtenus, statut (admis/ajourné/rattrapage)
- Filtres : session, promotion

### Onglet 12 — Bulletins
- Génération de bulletins individuels (PDF FPDF2) pour chaque étudiant
- En-tête : université, faculté, département, promotion, année académique
- Contenu : notes par UE/EC, moyennes, crédits, mention, rang
- **Téléchargement PV de délibérations** (PDF) : récapitulatif de tous les résultats de promotion
  - Colonnes : numéro étudiant, nom, notes UE, moyenne, crédits, statut

### Onglet 13 — Communiqués
- Rédaction et publication de communiqués pour les étudiants du département
- Modification / suppression d'un communiqué

### Onglet 14 — Délibérations
- Interface de délibération par session et promotion
- Validation manuelle des décisions (admis, redoublant, exclu)
- Génération du PV PDF

### Onglet 15 — Années Académiques
- Gestion des années académiques du département
- Activation / désactivation d'une année académique

### Onglet 16 — Analyses / Statistiques
- Taux de réussite par promotion, UE, EC
- Histogrammes de distribution des notes
- Taux de présence moyen

### Onglet 17 — QR Code Présences
- Tableau de bord des tokens QR actifs
- Liste des pointages effectués par code QR

### Onglet 18 — Messages
- Lecture des messages envoyés par les étudiants
- Réponse aux messages
- Compteur de messages non lus

### Onglet 19 — Frais de Scolarité
- Sous-onglet **Types de frais** : création / modification / suppression des catégories (inscription, scolarité, examens…)
- Sous-onglet **Paiements** : enregistrement des paiements par étudiant
- Sous-onglet **Suivi** : état des paiements par étudiant (payé / partiel / impayé)
- Sous-onglet **Statistiques** : montants collectés vs attendus, taux de recouvrement

---

## 5. Administration — Admin Faculté

> Rôle : `admin_faculte`
> Accès limité à sa faculté.
> Dashboard : `pages/8_Admin_Dashboard.py` — fonction `render_admin_faculte()`

- **Départements** : liste, création, modification, suppression des départements de la faculté
- **Professeurs** : liste des professeurs de la faculté, ajout/rattachement à un département
- **Admins département** : création de comptes admin département dans sa faculté
- **Communiqués** : publication de communiqués au niveau faculté

---

## 6. Administration — Admin Université

> Rôle : `admin_universite`
> Accès à toute l'université.
> Dashboard : `pages/8_Admin_Dashboard.py` — fonction `render_admin_universite()`

- **Facultés** : liste, création, modification, suppression des facultés
- **Départements** : liste globale (toutes facultés), création, modification
- **Professeurs** : liste globale, création de comptes professeur (email + mot de passe initial), rattachement à départements
- **Admins faculté/département** : création et gestion des comptes admins inférieurs
- **Étudiants** : vue globale des étudiants de l'université
- **Communiqués** : publication au niveau université
- **Gestion académique** : années académiques, calendrier
- **Analytiques** : statistiques globales (effectifs, taux de réussite par faculté/département)

---

## 7. Administration — Super Admin

> Rôle : `super_admin`
> Accès à toutes les universités de la plateforme.
> Dashboard : `pages/8_Admin_Dashboard.py` — fonction `render_super_admin()`

- **Universités** : liste, création, modification, suppression des universités
- **Comptes Admin Université** : création et gestion des comptes `admin_universite`
- **Vue globale** : statistiques multi-universités (nombre d'universités, facultés, étudiants, professeurs)
- **Analytiques plateforme** : indicateurs globaux d'utilisation

---

## 8. Modèle de données (résumé)

### Tables principales

| Table | Description |
|-------|-------------|
| `universities` | Universités |
| `faculties` | Facultés (rattachées à une université) |
| `departments` | Départements (rattachés à une faculté) |
| `programs` | Filières |
| `options` | Options (rattachées à une filière) |
| `promotions` | Promotions (classe d'étudiants) |
| `users` | Comptes admin + professeurs (role: super_admin / admin_universite / admin_faculte / admin_departement / professeur) |
| `students` | Comptes étudiants (avec student_number, password_hash) |
| `student_registry` | Enregistrement des étudiants avec infos académiques |
| `professors` | Profil professeur (lié à users) |
| `department_professors` | Rattachements professeur–département |
| `ue` | Unités d'Enseignement (group_label: A/B/C = Session 1/2/3) |
| `ec` | Éléments Constitutifs (rattachés à une UE) |
| `schedules` | Créneaux de cours (emploi du temps) |
| `rooms` | Salles |
| `grades` | Notes (student_id, ec_id, note, session) |
| `academic_years` | Années académiques |
| `results` | Résultats de délibération (moyenne, crédits, statut) |
| `attendance` | Présences (student_id, schedule_id, date, status) |
| `attendance_tokens` | Tokens QR de pointage (6 chars, 45 min, 1 par créneau actif) |
| `student_messages` | Messages étudiant → administration (sujet, corps, reply) |
| `fees` | Types de frais (par université) |
| `student_fees` | Paiements de frais par étudiant |
| `announcements` | Communiqués (niveau université/faculté/département) |
| `tps` | Travaux pratiques (créés par professeur, assignés à une promotion) |
| `documents` | Documents partagés par les professeurs |

### Conventions de code (accès DB)

```python
# Pattern standard pour toutes les requêtes
from db.connection import execute_query

rows = execute_query(sql, params, fetch="all")   # liste de dicts
row  = execute_query(sql, params, fetch="one")   # dict ou None
execute_query(sql, params, fetch="none")          # INSERT/UPDATE/DELETE
```

### Authentification

- Admins & Professeurs : table `users`, bcrypt hash, `st.session_state["current_user"]`
- Étudiants : table `students`, bcrypt hash, `st.session_state["current_student"]`
- Mot de passe par défaut étudiant = `student_number`
- Pas de JWT — sessions Streamlit in-memory (à remplacer par JWT/sessions Laravel)

---

## Notes pour la migration Laravel

1. **Garder PostgreSQL** (Neon en prod) plutôt que migrer vers MySQL — le schéma est déjà en PG.
2. **API REST Laravel** pour tous les accès données — les dashboards Streamlit seront remplacés par des vues Blade ou une SPA.
3. **Authentification** : utiliser Laravel Sanctum (tokens API) ou Breeze/Jetstream pour les sessions web.
4. **Rôles** : implémenter avec `spatie/laravel-permission` — 5 rôles admin + rôle étudiant séparé.
5. **PDF** : remplacer FPDF2 par `barryvdh/laravel-dompdf` ou `spatie/laravel-pdf`.
6. **QR Code** : package `simplesoftwareio/simple-qrcode` pour Laravel.
7. **Import Excel** : package `maatwebsite/excel` (Laravel Excel).
8. **Emails/Notifications** : Laravel Mail + Notifications (database channel pour les messages in-app).
