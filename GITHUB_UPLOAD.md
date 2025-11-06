# 🚀 GitHub'a Yükleme Talimatları

## Proje Yapısı
Proje artık GitHub'a yüklenmeye hazır! Tüm dosyalar düzgün organize edildi.

```
Car-Rental-Fleet-Maintenance-System/
├── domain/                    # Domain entities & value objects
├── services/                  # Business logic services
├── adapters/                  # External ports & adapters
├── tests/                     # Test suite
├── webapp/                    # Flask web interface
├── docs/                      # UML diagrams
├── demo.py                    # Demo script
├── README.md                  # Project documentation
├── PROJECT_DOCUMENTATION.md   # Detailed documentation
├── .gitignore                 # Git ignore rules
└── __init__.py               # Package initializer
```

## GitHub'a Yükleme Adımları

### 1. Git Repository Oluştur
```bash
cd /Users/cansomer/Desktop/Car-Rental-Fleet-Maintenance-System-CRFMS--main
git init
git add .
git commit -m "Initial commit: Complete CRFMS implementation with web UI"
```

### 2. GitHub'da Repository Oluştur
1. https://github.com adresine git
2. "New repository" butonuna tıkla
3. Repository name: `Car-Rental-Fleet-Maintenance-System`
4. Description: "Advanced Car Rental & Fleet Maintenance System with Python"
5. Public veya Private seç
6. **Create repository** tıkla

### 3. Remote Ekle ve Push Et
```bash
git remote add origin https://github.com/KULLANICI_ADIN/Car-Rental-Fleet-Maintenance-System.git
git branch -M main
git push -u origin main
```

## ✅ Hazır Özellikler

- ✅ Tüm SOLID principles uygulandı
- ✅ Strategy pattern ile composable pricing
- ✅ Idempotent operations (token-based)
- ✅ Injectable clock (deterministic testing)
- ✅ Complete audit logging
- ✅ 500km maintenance threshold
- ✅ 1-hour grace period for late returns
- ✅ All penalties (late fee, mileage, fuel)
- ✅ Conflict detection
- ✅ Web UI (Flask)
- ✅ Comprehensive test suite
- ✅ UML diagrams
- ✅ Complete documentation

## 🌐 Web UI Çalıştırma

```bash
cd Car-Rental-Fleet-Maintenance-System-CRFMS--main
source venv/bin/activate
python3 webapp/app.py
```

Tarayıcıda: http://localhost:5000

## 🧪 Test Çalıştırma

```bash
python3 -m pytest tests/
```

## 📝 Demo Çalıştırma

```bash
python3 demo.py
```

---

**Developed by İrem Aslan**
*AIN-3005 Advanced Python Programming - Bahçeşehir University*
