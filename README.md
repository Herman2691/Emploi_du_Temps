# 🎓 UniSchedule — Plateforme Multi-Universités

Plateforme web de gestion des emplois du temps universitaires.
**Stack :** Streamlit + PostgreSQL (Supabase) | **Hébergement :** Streamlit Community Cloud

---

## 🚀 Installation & Lancement

### 1. Prérequis
- Python 3.11+
- Un compte [Supabase](https://supabase.com) (gratuit)

### 2. Cloner et installer
```bash
git clone <votre-repo>
cd timetable_app
pip install -r requirements.txt
```

### 3. Configurer la base de données (Supabase)
1. Créez un projet sur [supabase.com](https://supabase.com)
2. Dans **SQL Editor**, copiez-collez le contenu de `schema.sql` et exécutez
3. Récupérez vos credentials dans **Settings > Database**

### 4. Configurer les secrets Streamlit
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

### 5. Lancer en local
```bash
streamlit run app.py
```

---

## 🔑 Connexion Super Admin (démo)
- **Email :** `superadmin@platform.com`
- **Mot de passe :** `Admin@1234`

> ⚠️ Changez ce mot de passe immédiatement en production !

---

## 📁 Structure du projet

```
timetable_app/
├── app.py                    # Point d'entrée & navigation
├── schema.sql                # Schéma DB complet
├── requirements.txt
├── .gitignore
│
├── pages/
│   ├── 1_Accueil.py          # Liste universités (public)
│   ├── 2_Facultes.py         # Liste facultés (public)
│   ├── 3_Departements.py     # Liste départements (public)
│   ├── 4_Promotions.py       # Liste promotions (public)
│   ├── 5_Classes.py          # Liste classes (public)
│   ├── 6_Emploi_du_Temps.py  # Grille horaire + cours + communiqués (public)
│   ├── 7_Admin_Login.py      # Connexion admin
│   └── 8_Admin_Dashboard.py  # Dashboard multi-rôles (auth)
│
├── db/
│   ├── connection.py         # Pool de connexions (singleton)
│   └── queries.py            # Toutes les requêtes SQL (par domaine)
│
├── utils/
│   ├── auth.py               # Authentification bcrypt + sessions
│   ├── role_guard.py         # RBAC — contrôle d'accès hiérarchique
│   └── components.py         # Composants UI réutilisables
│
└── .streamlit/
    └── secrets.toml          # ⚠️ NE PAS COMMITTER
```

---

## 👥 Hiérarchie des rôles

| Rôle | Périmètre | Gère |
|------|-----------|------|
| `super_admin` | Toute la plateforme | Universités, Admins université |
| `admin_universite` | Son université | Facultés, Admins faculté |
| `admin_faculte` | Sa faculté | Départements, Admins département |
| `admin_departement` | Son département | Promotions, Classes, Cours, Profs, EDT, Communiqués |

---

## 🚀 Déploiement Streamlit Community Cloud

1. Poussez votre code sur GitHub (sans `secrets.toml`)
2. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io)
3. Déployez votre repo
4. Dans **Settings > Secrets**, copiez le contenu de votre `secrets.toml`

---

## 🔒 Sécurité

- Mots de passe hashés avec **bcrypt** (rounds=12)
- Vérification de rôle à chaque action admin
- Accès hiérarchique strict (scope check)
- Connexion DB via variables d'environnement sécurisées (Streamlit Secrets)
- Requêtes SQL paramétrées (protection injection SQL)
- HTTPS natif sur Streamlit Cloud + Supabase

---

## 🔟 Évolutions futures

- Export PDF des emplois du temps
- Authentification étudiants
- Notifications email (SendGrid / Resend)
- Application mobile (PWA)
- Modèle SaaS multi-tenant
- Statistiques analytiques
