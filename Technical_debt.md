# Technical Debt Log

**Last Updated:** [Date]  
**Project:** Market Analysis Automation  
**Maintainer:** [Your Name]

---

## 🔴 High Priority (Security/Operational Risk)

### 1. Database Credentials in Source Code
**File:** `market_analysis_automation/config/config.py` (lines 33-35)  
**Issue:** Database server names hardcoded in source code  
**Risk:** Low (uses Windows Auth, internal servers only)  
**Recommendation:** Move to environment variables  
**Effort:** 2-3 hours  
**Status:** Not started  
**Related:** #123 (if you have issue tracking)

### 2. API Keys Stored in Database
**File:** Config loaded from `MA_AppConfig` table  
**Issue:** API keys (Google Maps, ArcGIS) stored in database instead of secure vault  
**Risk:** Medium  
**Recommendation:** Migrate to Azure Key Vault  
**Effort:** 1-2 days  
**Status:** Not started

### 3. No PROD Access Controls
**File:** `main.py`  
**Issue:** Any developer can run `--stage PROD` without checks  
**Risk:** Medium (accidental production changes)  
**Recommendation:** Add confirmation prompt and access control  
**Effort:** 3-4 hours  
**Status:** Not started

---

## 🟡 Medium Priority (Code Quality/Maintainability)

### 4. Excessive Error Swallowing
**File:** `server.py` (lines 280-355, many other locations)  
**Issue:** Every operation wrapped in `try/except` with errors logged but processing continues  
**Impact:** Hard to debug, may return incorrect results  
**Recommendation:** Remove excessive try/except, let FastAPI handle errors  
**Effort:** 2-3 days (gradual refactoring)  
**Status:** Not started

### 5. Monolithic Route File
**File:** `server.py` (400+ lines)  
**Issue:** All API routes in single file  
**Impact:** Hard to navigate, merge conflicts likely  
**Recommendation:** Split into router modules by domain  
**Effort:** 1-2 days  
**Status:** Not started

### 6. Large Model Files
**File:** `market_analysis_automation/models/models.py` (1000+ lines)  
**Issue:** All models in one massive file  
**Impact:** Hard to find specific models  
**Recommendation:** Split into domain-specific model files  
**Effort:** 4-6 hours  
**Status:** Not started

---

## 🟢 Low Priority (Nice-to-Have Improvements)

### 7. CORS Policy Too Permissive
**File:** `server.py` (line 66)  
**Issue:** `allow_origins=["*"]` with `allow_credentials=True`  
**Risk:** Low if internal-only deployment  
**Recommendation:** Restrict to specific origins  
**Effort:** 1-2 hours  
**Status:** Not started  
**Note:** Verify deployment model first (internal vs public)

### 8. Outdated README
**File:** `README.md`  
**Issue:** References non-existent files, mixes dev and prod instructions  
**Impact:** Confusing for new developers  
**Recommendation:** Rewrite with separate dev/deployment docs  
**Effort:** 3-4 hours  
**Status:** Not started

### 9. Unused Template Files
**File:** `templates/index.html`  
**Issue:** Template exists but isn't fully integrated  
**Impact:** Confusion about intended use  
**Recommendation:** Either complete the UI or remove the template  
**Effort:** TBD  
**Status:** Not started

### 10. Config Stored in Database
**File:** `market_analysis_automation/config/config.py`  
**Issue:** Application config loaded from database instead of files  
**Impact:** Hard to test locally, circular dependency on DB  
**Recommendation:** Move infrastructure config to files, keep only business rules in DB  
**Effort:** 1-2 weeks  
**Status:** Not started  
**Note:** This is architectural, requires pla