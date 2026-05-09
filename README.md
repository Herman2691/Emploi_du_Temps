# 🎓 UniSchedule — Plateforme de Gestion des Emplois du Temps Universitaires

Plateforme web complète de gestion des emplois du temps pour établissements multi-universités.  
**Stack :** Streamlit · PostgreSQL (Supabase) · Python 3.11  
**Hébergement :** Streamlit Community Cloud

---

## 🚀 Installation & Lancement

### Prérequis
- Python 3.11+
- Un compte [Supabase](https://supabase.com) (gratuit)

### 1. Cloner et installer

```bash
git clone https://github.com/Herman2691/Emploi_du_Temps.git
cd Emploi_du_Temps
pip install -r requirements.txt
```

### 2. Configurer la base de données

1. Créez un projet sur [supabase.com](https://supabase.com)
2. Dans **SQL Editor**, exécutez `schema.sql` pour créer toutes les tables
3. Appliquez les migrations `migration_v2.sql` → `migration_v30.sql` dans l'ordre

### 3. Configurer les secrets Streamlit

Éditez `.streamlit/secrets.toml` :

```toml
[postgres]
host     = "db.XXXX.supabase.co"
port     = 5432
database = "postgres"
user     = "postgres"
password = "VOTRE_MOT_DE_PASSE"
sslmode  = "require"
```

### 4. Lancer en local

```bash
streamlit run app.py
```

---

## 🔑 Accès démo

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| Super Admin | `superadmin@platform.com` | `Admin@1234` |

> ⚠️ Changez ce mot de passe immédiatement en production !

---

## 📁 Structure du projet

```
timetable_app/
├── app.py                      # Point d'entrée & navigation
├── schema.sql                  # Schéma DB complet (30 migrations)
├── generate_doc.py             # Génération de la documentation Word
├── requirements.txt
│
├── pages/
│   ├── 1_Accueil.py            # Liste des universités (public)
│   ├── 2_Horaire.py            # Grille horaire, cours & communiqués (public)
│   ├── 7_Admin_Login.py        # Connexion administrateurs
│   ├── 8_Admin_Dashboard.py    # Dashboard multi-rôles (auth)
│   ├── 9_Prof_Dashboard.py     # Espace professeur (auth)
│   ├── 10_Student_Auth.py      # Connexion étudiants
│   ├── 11_Student_Dashboard.py # Espace étudiant (auth)
│   └── 12_Prof_Auth.py         # Connexion professeurs
│
├── db/
│   ├── connection.py           # Pool de connexions ThreadedConnectionPool
│   └── queries.py              # Toutes les requêtes SQL (25+ classes)
│
├── utils/
│   ├── auth.py                 # Authentification bcrypt + sessions
│   ├── role_guard.py           # RBAC — contrôle d'accès hiérarchique
│   ├── components.py           # Composants UI réutilisables
│   ├── pdf_export.py           # Export PDF des emplois du temps
│   ├── ical_export.py          # Export iCal (.ics)
│   ├── notifications.py        # Système de notifications
│   └── storage.py              # Gestion fichiers (uploads)
│
└── .streamlit/
    └── secrets.toml            # ⚠️ NE PAS COMMITTER
```

---

## 👥 Hiérarchie des rôles

| Rôle | Périmètre | Responsabilités |
|------|-----------|-----------------|
| `super_admin` | Toute la plateforme | Gère les universités et les admins université |
| `admin_universite` | Son université | Facultés, admins faculté, pool de professeurs, comptes professeurs |
| `admin_faculte` | Sa faculté | Départements, admins département, affiliations professeurs |
| `admin_departement` | Son département | Promotions, classes, cours, UE, salles, emplois du temps, communiqués |
| `professeur` | Ses cours | Consulte son emploi du temps, gère TP/notes/présences/réclamations |
| `etudiant` | Sa promotion | Consulte son horaire, ses notes, ses bulletins |

---

## 🗄️ Base de données (30 migrations)

Principales tables :

| Domaine | Tables |
|---------|--------|
| Structure | `universities`, `faculties`, `departments`, `promotions`, `classes` |
| Enseignement | `courses`, `unite_enseignements`, `course_ue` |
| Emplois du temps | `schedules`, `rooms` |
| Personnes | `professors`, `professor_faculty_affiliations`, `students`, `users` |
| Évaluations | `evaluations`, `student_grades`, `attendance` |
| Contenu | `announcements`, `course_documents`, `student_claims` |
| Travaux | `tp_assignments`, `tp_submissions` |

---

## 🖥️ Fonctionnalités par espace

### Espace Public
- Consultation des universités, facultés et départements
- Affichage des emplois du temps par classe (grille hebdomadaire)
- Lecture des communiqués

### Espace Étudiant
- Connexion sécurisée (email + mot de passe hashé bcrypt)
- Emploi du temps personnel avec filtres (semaine, type de créneau)
- Consultation des notes et calcul automatique de la moyenne
- Téléchargement du bulletin de notes (PDF)
- Accès aux documents de cours déposés par les professeurs
- Suivi des présences
- Messagerie interne et réclamations

### Espace Professeur
- Emploi du temps personnel avec filtres (faculté, type, semaine paire/impaire)
- Gestion des documents de cours (upload)
- Gestion des TP (dépôt, correction)
- Saisie des notes
- Liste des classes avec fiches étudiants
- Suivi des présences
- Messagerie et gestion des réclamations étudiantes

### Espace Administrateur

**Super Admin**
- Gestion des universités (création, activation/désactivation)
- Gestion des comptes admin université

**Admin Université**
- Gestion des facultés
- Pool de professeurs de l'université (création, comptes de connexion)
- Registre étudiant multi-années (création, statuts académiques)
- Analytics (statistiques d'occupation, charge enseignante)
- Annonces

**Admin Faculté**
- Gestion des départements
- Affiliations des professeurs (permanent / visiteur)
- Vue étudiants en lecture seule
- Annonces

**Admin Département**
- Gestion des promotions et classes
- Gestion des cours et UE
- Gestion des salles
- Création et édition des emplois du temps
- Communiqués
- Vue comptes professeurs (lecture seule — création centralisée au niveau université)

---

## 📤 Exports disponibles

| Format | Contenu |
|--------|---------|
| PDF | Emploi du temps (vue hebdomadaire), bulletin de notes |
| iCal (.ics) | Emploi du temps compatible Google Calendar / Outlook |
| Word (.docx) | Documentation technique complète (`generate_doc.py`) |

---

## 🚀 Déploiement Streamlit Community Cloud

1. Poussez votre code sur GitHub (sans `secrets.toml`)
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io)
3. Déployez en sélectionnant `app.py` comme point d'entrée
4. Dans **Settings > Secrets**, copiez le contenu de votre `secrets.toml`

---

## 🔒 Sécurité

- Mots de passe hashés avec **bcrypt** (rounds=12)
- Vérification du rôle et du périmètre à chaque action
- Requêtes SQL entièrement paramétrées (protection injection SQL)
- Secrets gérés via Streamlit Secrets (jamais dans le code)
- HTTPS natif sur Streamlit Cloud + Supabase
- Pool de connexions ThreadedConnectionPool (max 10 connexions locales)
