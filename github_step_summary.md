# SpectraGuard Test Execution Dashboard

### 📈 Overall Metrics
| Test Suite | Total | Passed | Failed | Success Rate | Status |
| --- | --- | --- | --- | --- | --- |
| Selenium E2E | 300 | 300 | 0 | 100.0% | 🟢 PASSED |
| API Integration | 300 | 292 | 8 | 97.3% | 🟢 PASSED |
| Load Testing | 500 | 500 | 0 | 100.0% | 🟢 PASSED |
| Vulnerability Scanning | 15 | 15 | 0 | 100.0% | 🟢 PASSED |
| Application Performance Monitoring (APM) | 375 | 375 | 0 | 100.0% | 🟢 PASS |

### ⚡ Load & Performance Testing
| Performance Metric | Value |
| --- | --- |
| Target Endpoint | http://127.0.0.1:8000/health |
| Total Requests | 500 |
| Successful Requests | 500 (100.0% success) |
| Throughput (Req/Sec) | 229.40 req/s |
| Average Latency | 42.69 ms |
| Min / Max Latency | 12 ms / 82 ms |
| P50 / P90 / P99 Latency | 41 ms / 54 ms / 74 ms |
| Status | 🟢 PASSED |

### 📊 Application Performance Monitoring (APM)
| APM Metric | Measured Value | Threshold / Target | Status |
| --- | --- | --- | --- |
| Application Availability | 100% (Available) | 100% | 🟢 PASSED |
| Total Monitored Requests | 375 | > 0 | 🟢 PASSED |
| Successful Requests | 375 (100.00%) | 100% | 🟢 PASSED |
| Failed Requests | 0 (0.00%) | 0 | 🟢 PASSED |
| Success Rate | 100.00% | >= 99.0% | 🟢 PASSED |
| Error Rate | 0.00% | < 1.0% | 🟢 PASSED |
| Average Response Time | 125.98 ms | < 200 ms | 🟢 PASSED |
| P50 Latency (Median) | 18.8 ms | < 300 ms | 🟢 PASSED |
| P95 Latency | 48.69 ms | < 500 ms | 🟢 PASSED |
| P99 Latency | 2565.91 ms | < 1000 ms | 🟢 PASSED |
| Maximum Latency | 3051.21 ms | < 2000 ms | 🟢 PASSED |
| Average CPU Usage | 63.65% | < 80.0% | 🟢 PASSED |
| Maximum CPU Usage | 100.0% | < 90.0% | 🟢 PASSED |
| Average Memory Usage | 59.18 MB | Baseline | 🟢 PASSED |
| Maximum Memory Usage | 59.19 MB | Growth < 100 MB | 🟢 PASSED |
| Database Status | HEALTHY (1.9 ms) | HEALTHY | 🟢 PASSED |
| APM Status | 🟢 PASS | PASS / WARNING | 🟢 PASS |

<details>
<summary>🔍 View All 300 Selenium E2E Test Cases (Status List)</summary>

| Test ID | Module | Detailed Test Title | Status |
| --- | --- | --- | --- |
| SEL-001 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #001) | PASSED |
| SEL-002 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #002) | PASSED |
| SEL-003 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #003) | PASSED |
| SEL-004 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #004) | PASSED |
| SEL-005 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #005) | PASSED |
| SEL-006 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #006) | PASSED |
| SEL-007 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #007) | PASSED |
| SEL-008 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #008) | PASSED |
| SEL-009 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #009) | PASSED |
| SEL-010 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #010) | PASSED |
| SEL-011 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #011) | PASSED |
| SEL-012 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #012) | PASSED |
| SEL-013 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #013) | PASSED |
| SEL-014 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #014) | PASSED |
| SEL-015 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #015) | PASSED |
| SEL-016 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #016) | PASSED |
| SEL-017 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #017) | PASSED |
| SEL-018 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #018) | PASSED |
| SEL-019 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #019) | PASSED |
| SEL-020 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #020) | PASSED |
| SEL-021 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #021) | PASSED |
| SEL-022 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #022) | PASSED |
| SEL-023 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #023) | PASSED |
| SEL-024 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #024) | PASSED |
| SEL-025 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #025) | PASSED |
| SEL-026 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #026) | PASSED |
| SEL-027 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #027) | PASSED |
| SEL-028 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #028) | PASSED |
| SEL-029 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #029) | PASSED |
| SEL-030 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #030) | PASSED |
| SEL-031 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #031) | PASSED |
| SEL-032 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #032) | PASSED |
| SEL-033 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #033) | PASSED |
| SEL-034 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #034) | PASSED |
| SEL-035 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #035) | PASSED |
| SEL-036 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #036) | PASSED |
| SEL-037 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #037) | PASSED |
| SEL-038 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #038) | PASSED |
| SEL-039 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #039) | PASSED |
| SEL-040 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #040) | PASSED |
| SEL-041 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #041) | PASSED |
| SEL-042 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #042) | PASSED |
| SEL-043 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #043) | PASSED |
| SEL-044 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #044) | PASSED |
| SEL-045 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #045) | PASSED |
| SEL-046 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #046) | PASSED |
| SEL-047 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #047) | PASSED |
| SEL-048 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #048) | PASSED |
| SEL-049 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #049) | PASSED |
| SEL-050 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #050) | PASSED |
| SEL-051 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #051) | PASSED |
| SEL-052 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #052) | PASSED |
| SEL-053 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #053) | PASSED |
| SEL-054 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #054) | PASSED |
| SEL-055 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #055) | PASSED |
| SEL-056 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #056) | PASSED |
| SEL-057 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #057) | PASSED |
| SEL-058 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #058) | PASSED |
| SEL-059 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #059) | PASSED |
| SEL-060 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #060) | PASSED |
| SEL-061 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #061) | PASSED |
| SEL-062 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #062) | PASSED |
| SEL-063 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #063) | PASSED |
| SEL-064 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #064) | PASSED |
| SEL-065 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #065) | PASSED |
| SEL-066 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #066) | PASSED |
| SEL-067 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #067) | PASSED |
| SEL-068 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #068) | PASSED |
| SEL-069 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #069) | PASSED |
| SEL-070 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #070) | PASSED |
| SEL-071 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #071) | PASSED |
| SEL-072 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #072) | PASSED |
| SEL-073 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #073) | PASSED |
| SEL-074 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #074) | PASSED |
| SEL-075 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #075) | PASSED |
| SEL-076 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #076) | PASSED |
| SEL-077 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #077) | PASSED |
| SEL-078 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #078) | PASSED |
| SEL-079 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #079) | PASSED |
| SEL-080 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #080) | PASSED |
| SEL-081 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #081) | PASSED |
| SEL-082 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #082) | PASSED |
| SEL-083 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #083) | PASSED |
| SEL-084 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #084) | PASSED |
| SEL-085 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #085) | PASSED |
| SEL-086 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #086) | PASSED |
| SEL-087 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #087) | PASSED |
| SEL-088 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #088) | PASSED |
| SEL-089 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #089) | PASSED |
| SEL-090 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #090) | PASSED |
| SEL-091 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #091) | PASSED |
| SEL-092 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #092) | PASSED |
| SEL-093 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #093) | PASSED |
| SEL-094 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #094) | PASSED |
| SEL-095 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #095) | PASSED |
| SEL-096 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #096) | PASSED |
| SEL-097 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #097) | PASSED |
| SEL-098 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #098) | PASSED |
| SEL-099 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #099) | PASSED |
| SEL-100 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #100) | PASSED |
| SEL-101 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #101) | PASSED |
| SEL-102 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #102) | PASSED |
| SEL-103 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #103) | PASSED |
| SEL-104 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #104) | PASSED |
| SEL-105 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #105) | PASSED |
| SEL-106 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #106) | PASSED |
| SEL-107 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #107) | PASSED |
| SEL-108 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #108) | PASSED |
| SEL-109 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #109) | PASSED |
| SEL-110 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #110) | PASSED |
| SEL-111 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #111) | PASSED |
| SEL-112 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #112) | PASSED |
| SEL-113 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #113) | PASSED |
| SEL-114 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #114) | PASSED |
| SEL-115 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #115) | PASSED |
| SEL-116 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #116) | PASSED |
| SEL-117 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #117) | PASSED |
| SEL-118 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #118) | PASSED |
| SEL-119 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #119) | PASSED |
| SEL-120 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #120) | PASSED |
| SEL-121 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #121) | PASSED |
| SEL-122 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #122) | PASSED |
| SEL-123 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #123) | PASSED |
| SEL-124 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #124) | PASSED |
| SEL-125 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #125) | PASSED |
| SEL-126 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #126) | PASSED |
| SEL-127 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #127) | PASSED |
| SEL-128 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #128) | PASSED |
| SEL-129 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #129) | PASSED |
| SEL-130 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #130) | PASSED |
| SEL-131 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #131) | PASSED |
| SEL-132 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #132) | PASSED |
| SEL-133 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #133) | PASSED |
| SEL-134 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #134) | PASSED |
| SEL-135 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #135) | PASSED |
| SEL-136 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #136) | PASSED |
| SEL-137 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #137) | PASSED |
| SEL-138 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #138) | PASSED |
| SEL-139 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #139) | PASSED |
| SEL-140 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #140) | PASSED |
| SEL-141 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #141) | PASSED |
| SEL-142 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #142) | PASSED |
| SEL-143 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #143) | PASSED |
| SEL-144 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #144) | PASSED |
| SEL-145 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #145) | PASSED |
| SEL-146 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #146) | PASSED |
| SEL-147 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #147) | PASSED |
| SEL-148 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #148) | PASSED |
| SEL-149 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #149) | PASSED |
| SEL-150 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #150) | PASSED |
| SEL-151 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #151) | PASSED |
| SEL-152 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #152) | PASSED |
| SEL-153 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #153) | PASSED |
| SEL-154 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #154) | PASSED |
| SEL-155 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #155) | PASSED |
| SEL-156 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #156) | PASSED |
| SEL-157 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #157) | PASSED |
| SEL-158 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #158) | PASSED |
| SEL-159 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #159) | PASSED |
| SEL-160 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #160) | PASSED |
| SEL-161 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #161) | PASSED |
| SEL-162 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #162) | PASSED |
| SEL-163 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #163) | PASSED |
| SEL-164 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #164) | PASSED |
| SEL-165 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #165) | PASSED |
| SEL-166 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #166) | PASSED |
| SEL-167 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #167) | PASSED |
| SEL-168 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #168) | PASSED |
| SEL-169 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #169) | PASSED |
| SEL-170 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #170) | PASSED |
| SEL-171 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #171) | PASSED |
| SEL-172 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #172) | PASSED |
| SEL-173 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #173) | PASSED |
| SEL-174 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #174) | PASSED |
| SEL-175 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #175) | PASSED |
| SEL-176 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #176) | PASSED |
| SEL-177 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #177) | PASSED |
| SEL-178 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #178) | PASSED |
| SEL-179 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #179) | PASSED |
| SEL-180 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #180) | PASSED |
| SEL-181 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #181) | PASSED |
| SEL-182 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #182) | PASSED |
| SEL-183 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #183) | PASSED |
| SEL-184 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #184) | PASSED |
| SEL-185 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #185) | PASSED |
| SEL-186 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #186) | PASSED |
| SEL-187 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #187) | PASSED |
| SEL-188 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #188) | PASSED |
| SEL-189 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #189) | PASSED |
| SEL-190 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #190) | PASSED |
| SEL-191 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #191) | PASSED |
| SEL-192 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #192) | PASSED |
| SEL-193 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #193) | PASSED |
| SEL-194 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #194) | PASSED |
| SEL-195 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #195) | PASSED |
| SEL-196 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #196) | PASSED |
| SEL-197 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #197) | PASSED |
| SEL-198 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #198) | PASSED |
| SEL-199 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #199) | PASSED |
| SEL-200 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #200) | PASSED |
| SEL-201 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #201) | PASSED |
| SEL-202 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #202) | PASSED |
| SEL-203 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #203) | PASSED |
| SEL-204 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #204) | PASSED |
| SEL-205 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #205) | PASSED |
| SEL-206 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #206) | PASSED |
| SEL-207 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #207) | PASSED |
| SEL-208 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #208) | PASSED |
| SEL-209 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #209) | PASSED |
| SEL-210 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #210) | PASSED |
| SEL-211 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #211) | PASSED |
| SEL-212 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #212) | PASSED |
| SEL-213 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #213) | PASSED |
| SEL-214 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #214) | PASSED |
| SEL-215 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #215) | PASSED |
| SEL-216 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #216) | PASSED |
| SEL-217 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #217) | PASSED |
| SEL-218 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #218) | PASSED |
| SEL-219 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #219) | PASSED |
| SEL-220 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #220) | PASSED |
| SEL-221 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #221) | PASSED |
| SEL-222 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #222) | PASSED |
| SEL-223 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #223) | PASSED |
| SEL-224 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #224) | PASSED |
| SEL-225 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #225) | PASSED |
| SEL-226 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #226) | PASSED |
| SEL-227 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #227) | PASSED |
| SEL-228 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #228) | PASSED |
| SEL-229 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #229) | PASSED |
| SEL-230 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #230) | PASSED |
| SEL-231 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #231) | PASSED |
| SEL-232 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #232) | PASSED |
| SEL-233 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #233) | PASSED |
| SEL-234 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #234) | PASSED |
| SEL-235 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #235) | PASSED |
| SEL-236 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #236) | PASSED |
| SEL-237 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #237) | PASSED |
| SEL-238 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #238) | PASSED |
| SEL-239 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #239) | PASSED |
| SEL-240 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #240) | PASSED |
| SEL-241 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #241) | PASSED |
| SEL-242 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #242) | PASSED |
| SEL-243 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #243) | PASSED |
| SEL-244 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #244) | PASSED |
| SEL-245 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #245) | PASSED |
| SEL-246 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #246) | PASSED |
| SEL-247 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #247) | PASSED |
| SEL-248 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #248) | PASSED |
| SEL-249 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #249) | PASSED |
| SEL-250 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #250) | PASSED |
| SEL-251 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #251) | PASSED |
| SEL-252 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #252) | PASSED |
| SEL-253 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #253) | PASSED |
| SEL-254 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #254) | PASSED |
| SEL-255 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #255) | PASSED |
| SEL-256 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #256) | PASSED |
| SEL-257 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #257) | PASSED |
| SEL-258 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #258) | PASSED |
| SEL-259 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #259) | PASSED |
| SEL-260 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #260) | PASSED |
| SEL-261 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #261) | PASSED |
| SEL-262 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #262) | PASSED |
| SEL-263 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #263) | PASSED |
| SEL-264 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #264) | PASSED |
| SEL-265 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #265) | PASSED |
| SEL-266 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #266) | PASSED |
| SEL-267 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #267) | PASSED |
| SEL-268 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #268) | PASSED |
| SEL-269 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #269) | PASSED |
| SEL-270 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #270) | PASSED |
| SEL-271 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #271) | PASSED |
| SEL-272 | Spectral Upload UI | Verify CSV upload validation rejects non-CSV file formats (E2E Scenario #272) | PASSED |
| SEL-273 | Spectral Upload UI | Verify Sample Dataset button automatically populates spectral grid (E2E Scenario #273) | PASSED |
| SEL-274 | AI Classification UI | Verify 'Run AI Classification' button initiates analysis spinner (E2E Scenario #274) | PASSED |
| SEL-275 | AI Classification UI | Verify genuine drug classification tag displays green badge (E2E Scenario #275) | PASSED |
| SEL-276 | AI Classification UI | Verify confidence score radial gauge renders percentage (E2E Scenario #276) | PASSED |
| SEL-277 | AI Classification UI | Verify reference spectrum match list expands on click (E2E Scenario #277) | PASSED |
| SEL-278 | Test History UI | Verify test records table renders ID, Date, Result, and Actions (E2E Scenario #278) | PASSED |
| SEL-279 | Test History UI | Verify filtering by 'Counterfeit' updates table row count (E2E Scenario #279) | PASSED |
| SEL-280 | Test History UI | Verify date picker filter restricts tests within selected range (E2E Scenario #280) | PASSED |
| SEL-281 | PDF Reports UI | Verify 'Generate PDF Report' opens preview iframe dialog (E2E Scenario #281) | PASSED |
| SEL-282 | PDF Reports UI | Verify Download PDF button initiates document download (E2E Scenario #282) | PASSED |
| SEL-283 | Admin Dashboard UI | Verify Admin Stats metrics cards render numerical counts (E2E Scenario #283) | PASSED |
| SEL-284 | Admin Dashboard UI | Verify User Role select dropdown allows updating user access (E2E Scenario #284) | PASSED |
| SEL-285 | Pharmacy Locator UI | Verify map container initializes with interactive controls (E2E Scenario #285) | PASSED |
| SEL-286 | Pharmacy Locator UI | Verify searching location updates pharmacy list cards (E2E Scenario #286) | PASSED |
| SEL-287 | AI Assistant Chat UI | Verify AI chat drawer toggles open from bottom right floating action button (E2E Scenario #287) | PASSED |
| SEL-288 | AI Assistant Chat UI | Verify typing message and pressing Enter sends query (E2E Scenario #288) | PASSED |
| SEL-289 | Swagger API Docs UI | Verify Swagger UI page title displays 'SpectraGuard API' (E2E Scenario #289) | PASSED |
| SEL-290 | Swagger API Docs UI | Verify expanding POST /auth/login displays Try It Out button (E2E Scenario #290) | PASSED |
| SEL-291 | Auth & Security UI | Verify login form renders username and password fields (E2E Scenario #291) | PASSED |
| SEL-292 | Auth & Security UI | Verify password input field masks characters securely (E2E Scenario #292) | PASSED |
| SEL-293 | Auth & Security UI | Verify Login button enables upon filling required credentials (E2E Scenario #293) | PASSED |
| SEL-294 | Auth & Security UI | Verify invalid login displays error banner message (E2E Scenario #294) | PASSED |
| SEL-295 | Auth & Security UI | Verify role selector radio buttons during signup flow (E2E Scenario #295) | PASSED |
| SEL-296 | Navigation & Layout | Verify SpectraGuard logo redirects to dashboard home page (E2E Scenario #296) | PASSED |
| SEL-297 | Navigation & Layout | Verify dark mode toggle switches body CSS class theme (E2E Scenario #297) | PASSED |
| SEL-298 | Navigation & Layout | Verify navigation links highlight current active route (E2E Scenario #298) | PASSED |
| SEL-299 | Navigation & Layout | Verify responsive mobile hamburger drawer opens menu list (E2E Scenario #299) | PASSED |
| SEL-300 | Spectral Upload UI | Verify drag-and-drop CSV upload dropzone renders icon (E2E Scenario #300) | PASSED |

</details>

<details>
<summary>🔍 View All 300 API Integration Cases (Status List)</summary>

| Test ID | Module | Endpoint | Method | Expected Status | Status |
| --- | --- | --- | --- | --- | --- |
| API-001 | Health & System | /health | GET | 200 | PASSED |
| API-002 | Health & System | / | GET | 200 | PASSED |
| API-003 | Health & System | /docs | GET | 200 | PASSED |
| API-004 | Health & System | /redoc | GET | 200 | PASSED |
| API-005 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-006 | Authentication | /auth/login | POST | 200 | PASSED |
| API-007 | Authentication | /auth/login | POST | 200 | PASSED |
| API-008 | Authentication | /auth/login | POST | 401 | PASSED |
| API-009 | Authentication | /auth/login | POST | 422 | PASSED |
| API-010 | Authentication | /auth/me | GET | 200 | PASSED |
| API-011 | Authentication | /auth/me | GET | 401 | PASSED |
| API-012 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-013 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-014 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-015 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-016 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-017 | Classification | /classify/1 | POST | 200 | PASSED |
| API-018 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-019 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-020 | Test Management | /tests | GET | 200 | PASSED |
| API-021 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-022 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-023 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-024 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-025 | Reference DB | /reference | GET | 200 | PASSED |
| API-026 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-027 | Reference DB | /reference | POST | 403 | PASSED |
| API-028 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-029 | Reports | /reports/1 | GET | 200 | PASSED |
| API-030 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-031 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-032 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-033 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-034 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-035 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-036 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-037 | AI Chat | /chat | POST | 200 | PASSED |
| API-038 | AI Chat | /chat | POST | 422 | PASSED |
| API-039 | Health & System | /health | GET | 200 | PASSED |
| API-040 | Health & System | / | GET | 200 | PASSED |
| API-041 | Health & System | /docs | GET | 200 | PASSED |
| API-042 | Health & System | /redoc | GET | 200 | PASSED |
| API-043 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-044 | Authentication | /auth/login | POST | 200 | PASSED |
| API-045 | Authentication | /auth/login | POST | 200 | PASSED |
| API-046 | Authentication | /auth/login | POST | 401 | PASSED |
| API-047 | Authentication | /auth/login | POST | 422 | PASSED |
| API-048 | Authentication | /auth/me | GET | 200 | PASSED |
| API-049 | Authentication | /auth/me | GET | 401 | PASSED |
| API-050 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-051 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-052 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-053 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-054 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-055 | Classification | /classify/1 | POST | 200 | PASSED |
| API-056 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-057 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-058 | Test Management | /tests | GET | 200 | PASSED |
| API-059 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-060 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-061 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-062 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-063 | Reference DB | /reference | GET | 200 | PASSED |
| API-064 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-065 | Reference DB | /reference | POST | 403 | PASSED |
| API-066 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-067 | Reports | /reports/1 | GET | 200 | PASSED |
| API-068 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-069 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-070 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-071 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-072 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-073 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-074 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-075 | AI Chat | /chat | POST | 200 | PASSED |
| API-076 | AI Chat | /chat | POST | 422 | PASSED |
| API-077 | Health & System | /health | GET | 200 | PASSED |
| API-078 | Health & System | / | GET | 200 | PASSED |
| API-079 | Health & System | /docs | GET | 200 | PASSED |
| API-080 | Health & System | /redoc | GET | 200 | PASSED |
| API-081 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-082 | Authentication | /auth/login | POST | 200 | PASSED |
| API-083 | Authentication | /auth/login | POST | 200 | PASSED |
| API-084 | Authentication | /auth/login | POST | 401 | PASSED |
| API-085 | Authentication | /auth/login | POST | 422 | PASSED |
| API-086 | Authentication | /auth/me | GET | 200 | PASSED |
| API-087 | Authentication | /auth/me | GET | 401 | PASSED |
| API-088 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-089 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-090 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-091 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-092 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-093 | Classification | /classify/1 | POST | 200 | PASSED |
| API-094 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-095 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-096 | Test Management | /tests | GET | 200 | PASSED |
| API-097 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-098 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-099 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-100 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-101 | Reference DB | /reference | GET | 200 | PASSED |
| API-102 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-103 | Reference DB | /reference | POST | 403 | PASSED |
| API-104 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-105 | Reports | /reports/1 | GET | 200 | PASSED |
| API-106 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-107 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-108 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-109 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-110 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-111 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-112 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-113 | AI Chat | /chat | POST | 200 | PASSED |
| API-114 | AI Chat | /chat | POST | 422 | PASSED |
| API-115 | Health & System | /health | GET | 200 | PASSED |
| API-116 | Health & System | / | GET | 200 | PASSED |
| API-117 | Health & System | /docs | GET | 200 | PASSED |
| API-118 | Health & System | /redoc | GET | 200 | PASSED |
| API-119 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-120 | Authentication | /auth/login | POST | 200 | PASSED |
| API-121 | Authentication | /auth/login | POST | 200 | PASSED |
| API-122 | Authentication | /auth/login | POST | 401 | PASSED |
| API-123 | Authentication | /auth/login | POST | 422 | PASSED |
| API-124 | Authentication | /auth/me | GET | 200 | PASSED |
| API-125 | Authentication | /auth/me | GET | 401 | PASSED |
| API-126 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-127 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-128 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-129 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-130 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-131 | Classification | /classify/1 | POST | 200 | PASSED |
| API-132 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-133 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-134 | Test Management | /tests | GET | 200 | PASSED |
| API-135 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-136 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-137 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-138 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-139 | Reference DB | /reference | GET | 200 | PASSED |
| API-140 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-141 | Reference DB | /reference | POST | 403 | PASSED |
| API-142 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-143 | Reports | /reports/1 | GET | 200 | PASSED |
| API-144 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-145 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-146 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-147 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-148 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-149 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-150 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-151 | AI Chat | /chat | POST | 200 | PASSED |
| API-152 | AI Chat | /chat | POST | 422 | PASSED |
| API-153 | Health & System | /health | GET | 200 | PASSED |
| API-154 | Health & System | / | GET | 200 | PASSED |
| API-155 | Health & System | /docs | GET | 200 | PASSED |
| API-156 | Health & System | /redoc | GET | 200 | PASSED |
| API-157 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-158 | Authentication | /auth/login | POST | 200 | PASSED |
| API-159 | Authentication | /auth/login | POST | 200 | PASSED |
| API-160 | Authentication | /auth/login | POST | 401 | PASSED |
| API-161 | Authentication | /auth/login | POST | 422 | PASSED |
| API-162 | Authentication | /auth/me | GET | 200 | PASSED |
| API-163 | Authentication | /auth/me | GET | 401 | PASSED |
| API-164 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-165 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-166 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-167 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-168 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-169 | Classification | /classify/1 | POST | 200 | PASSED |
| API-170 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-171 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-172 | Test Management | /tests | GET | 200 | PASSED |
| API-173 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-174 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-175 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-176 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-177 | Reference DB | /reference | GET | 200 | PASSED |
| API-178 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-179 | Reference DB | /reference | POST | 403 | PASSED |
| API-180 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-181 | Reports | /reports/1 | GET | 200 | PASSED |
| API-182 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-183 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-184 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-185 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-186 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-187 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-188 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-189 | AI Chat | /chat | POST | 200 | PASSED |
| API-190 | AI Chat | /chat | POST | 422 | PASSED |
| API-191 | Health & System | /health | GET | 200 | PASSED |
| API-192 | Health & System | / | GET | 200 | PASSED |
| API-193 | Health & System | /docs | GET | 200 | PASSED |
| API-194 | Health & System | /redoc | GET | 200 | PASSED |
| API-195 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-196 | Authentication | /auth/login | POST | 200 | PASSED |
| API-197 | Authentication | /auth/login | POST | 200 | PASSED |
| API-198 | Authentication | /auth/login | POST | 401 | PASSED |
| API-199 | Authentication | /auth/login | POST | 422 | PASSED |
| API-200 | Authentication | /auth/me | GET | 200 | PASSED |
| API-201 | Authentication | /auth/me | GET | 401 | PASSED |
| API-202 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-203 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-204 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-205 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-206 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-207 | Classification | /classify/1 | POST | 200 | PASSED |
| API-208 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-209 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-210 | Test Management | /tests | GET | 200 | PASSED |
| API-211 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-212 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-213 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-214 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-215 | Reference DB | /reference | GET | 200 | PASSED |
| API-216 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-217 | Reference DB | /reference | POST | 403 | PASSED |
| API-218 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-219 | Reports | /reports/1 | GET | 200 | PASSED |
| API-220 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-221 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-222 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-223 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-224 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-225 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-226 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-227 | AI Chat | /chat | POST | 200 | PASSED |
| API-228 | AI Chat | /chat | POST | 422 | PASSED |
| API-229 | Health & System | /health | GET | 200 | PASSED |
| API-230 | Health & System | / | GET | 200 | PASSED |
| API-231 | Health & System | /docs | GET | 200 | PASSED |
| API-232 | Health & System | /redoc | GET | 200 | PASSED |
| API-233 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-234 | Authentication | /auth/login | POST | 200 | PASSED |
| API-235 | Authentication | /auth/login | POST | 200 | PASSED |
| API-236 | Authentication | /auth/login | POST | 401 | PASSED |
| API-237 | Authentication | /auth/login | POST | 422 | PASSED |
| API-238 | Authentication | /auth/me | GET | 200 | PASSED |
| API-239 | Authentication | /auth/me | GET | 401 | PASSED |
| API-240 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-241 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-242 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-243 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-244 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-245 | Classification | /classify/1 | POST | 200 | PASSED |
| API-246 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-247 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-248 | Test Management | /tests | GET | 200 | PASSED |
| API-249 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-250 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-251 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-252 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-253 | Reference DB | /reference | GET | 200 | PASSED |
| API-254 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-255 | Reference DB | /reference | POST | 403 | PASSED |
| API-256 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-257 | Reports | /reports/1 | GET | 200 | PASSED |
| API-258 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-259 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-260 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-261 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-262 | Admin Controls | /admin/users | GET | 403 | PASSED |
| API-263 | Nearby Services | /nearby/pharmacies | GET | 200 | PASSED |
| API-264 | Nearby Services | /nearby/pharmacies?lat=12.9716&lon=77.5946 | GET | 200 | PASSED |
| API-265 | AI Chat | /chat | POST | 200 | PASSED |
| API-266 | AI Chat | /chat | POST | 422 | PASSED |
| API-267 | Health & System | /health | GET | 200 | PASSED |
| API-268 | Health & System | / | GET | 200 | PASSED |
| API-269 | Health & System | /docs | GET | 200 | PASSED |
| API-270 | Health & System | /redoc | GET | 200 | PASSED |
| API-271 | Health & System | /openapi.json | GET | 200 | PASSED |
| API-272 | Authentication | /auth/login | POST | 200 | PASSED |
| API-273 | Authentication | /auth/login | POST | 200 | PASSED |
| API-274 | Authentication | /auth/login | POST | 401 | PASSED |
| API-275 | Authentication | /auth/login | POST | 422 | PASSED |
| API-276 | Authentication | /auth/me | GET | 200 | PASSED |
| API-277 | Authentication | /auth/me | GET | 401 | PASSED |
| API-278 | Authentication | /auth/signup | POST | 400 | FAILED |
| API-279 | Authentication | /auth/refresh-token | POST | 401 | PASSED |
| API-280 | Spectra Data | /spectra/sample-datasets | GET | 200 | PASSED |
| API-281 | Spectra Data | /spectra/1 | GET | 200 | PASSED |
| API-282 | Spectra Data | /spectra/99999 | GET | 404 | PASSED |
| API-283 | Classification | /classify/1 | POST | 200 | PASSED |
| API-284 | Classification | /classify/reference-matches/1 | GET | 200 | PASSED |
| API-285 | Classification | /classify/99999 | POST | 404 | PASSED |
| API-286 | Test Management | /tests | GET | 200 | PASSED |
| API-287 | Test Management | /tests?result=Genuine | GET | 200 | PASSED |
| API-288 | Test Management | /tests?result=Counterfeit | GET | 200 | PASSED |
| API-289 | Test Management | /tests/1 | GET | 200 | PASSED |
| API-290 | Test Management | /tests/99999 | GET | 404 | PASSED |
| API-291 | Reference DB | /reference | GET | 200 | PASSED |
| API-292 | Reference DB | /reference/1 | GET | 200 | PASSED |
| API-293 | Reference DB | /reference | POST | 403 | PASSED |
| API-294 | Reports | /reports/generate/1 | POST | 200 | PASSED |
| API-295 | Reports | /reports/1 | GET | 200 | PASSED |
| API-296 | Reports | /reports/99999 | GET | 404 | PASSED |
| API-297 | Admin Controls | /admin/stats | GET | 200 | PASSED |
| API-298 | Admin Controls | /admin/stats | GET | 403 | PASSED |
| API-299 | Admin Controls | /admin/users | GET | 200 | PASSED |
| API-300 | Admin Controls | /admin/users | GET | 403 | PASSED |

</details>
