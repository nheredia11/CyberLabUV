# Scenario Design and Pedagogical Alignment (OE1)

## 1. Introduction and Methodological Framework
The **CyberLabUV** platform implements a structured scenario-based learning model designed for undergraduate cybersecurity education. Each scenario isolates a specific threat vector or vulnerability class, bridging theoretical security concepts with hands-on containerized experimentation. 

The pedagogical design is mapped against three internationally recognized cybersecurity frameworks:
* **MITRE ATT&CK**: For adversary tactics and techniques mapping.
* **NIST Cybersecurity Framework (CSF)**: For alignment with core security functions (Identify, Protect, Detect, Respond, Recover).
* **OWASP Top 10 (2021)**: For application-layer vulnerability classification.

---

## 2. Scenario Catalog Matrix (S01 – S05)

### S01: Network Reconnaissance (`recon`)
* **Learning Objective**: Identify active hosts, open ports, and running services on a target network segment using standard enumeration tools.
* **MITRE ATT&CK**: 
  * *Tactic*: Reconnaissance (TA0043)
  * *Technique*: Active Scanning: Network Service Discovery (T1046)
* **NIST CSF Function**: Identify (ID.AM - Asset Management) / Protect (PR.DS - Data Security)
* **OWASP Top 10**: Not applicable (Network/Infrastructure tier).
* **Vulnerable Component**: Misconfigured network perimeter exposing unauthenticated discovery services.
* **Tools Used**: `nmap`, `ping`, `dig`, `netstat`.
* **Checkpoints & Competency Levels**:
  * `CP01`: Execute host discovery $\rightarrow$ *Level: Initial*
  * `CP02`: Perform port scanning and service version detection $\rightarrow$ *Level: Autonomous*
* **Defensive Takeaway**: Disabling unnecessary network services and implementing strict firewall segmentation to reduce attack surface.

### S02: Vulnerable HTTP Authentication (`auth_http`)
* **Learning Objective**: Demonstrate the risks of weak credentials and unencrypted basic authentication headers over HTTP.
* **MITRE ATT&CK**: 
  * *Tactic*: Credential Access (TA0006)
  * *Technique*: Brute Force: Password Guessing (T1110.001)
* **NIST CSF Function**: Protect (PR.AC - Access Control) / Detect (DE.CM - Security Continuous Monitoring)
* **OWASP Top 10 (2021)**: A07:2021 - Identification and Authentication Failures
* **Vulnerable Component**: Flask web application accepting weak/default credentials via HTTP Basic Auth without rate limiting.
* **Tools Used**: `curl`, `hydra`.
* **Checkpoints & Competency Levels**:
  * `CP01`: Intercept HTTP authentication flow $\rightarrow$ *Level: Initial*
  * `CP02`: Execute credential brute-force attack against login endpoint $\rightarrow$ *Level: Autonomous*
* **Defensive Takeaway**: Enforcing multi-factor authentication (MFA), strong password policies, account lockout mechanisms, and mandatory TLS encryption.

### S03: OWASP Top 10 Web Vulnerabilities (`web_owasp`)
* **Learning Objective**: Identify and exploit common web application flaws (such as injection and improper input validation).
* **MITRE ATT&CK**: 
  * *Tactic*: Initial Access (TA0001) / Execution (TA0002)
  * *Technique*: Exploit Public-Facing Application (T1190)
* **NIST CSF Function**: Protect (PR.PT - Protective Technology)
* **OWASP Top 10 (2021)**: A03:2021 - Injection / A01:2021 - Broken Access Control
* **Vulnerable Component**: Web application processing unsanitized user input in backend database queries.
* **Tools Used**: `curl`, `grep`, custom payloads.
* **Checkpoints & Competency Levels**:
  * `CP01`: Identify injection vulnerability through input fuzzing $\rightarrow$ *Level: Initial*
  * `CP02`: Extract unauthorized data via crafted payload $\rightarrow$ *Level: Autonomous*
* **Defensive Takeaway**: Implementing parameterized queries (prepared statements), strict input validation, and output encoding.

### S04: Authentication Services (SSH / FTP) (`auth_services`)
* **Learning Objective**: Evaluate the security posture of remote management services exposed on standard ports.
* **MITRE ATT&CK**: 
  * *Tactic*: Credential Access (TA0006)
  * *Technique*: Brute Force (T1110)
* **NIST CSF Function**: Protect (PR.AC) / Detect (DE.CM)
* **OWASP Top 10 (2021)**: A07:2021 - Identification and Authentication Failures
* **Vulnerable Component**: Misconfigured SSH/FTP service containers with weak credentials.
* **Tools Used**: `nmap`, `hydra`, `nc`.
* **Checkpoints & Competency Levels**:
  * `CP01`: Enumerate remote administration ports $\rightarrow$ *Level: Initial*
  * `CP02`: Gain unauthorized access via credential dictionary attack $\rightarrow$ *Level: Autonomous*
* **Defensive Takeaway**: Disabling root password login over SSH, enforcing SSH key-based authentication, and utilizing fail2ban.

### S05: Man-in-the-Middle on Unencrypted Traffic (`mitm_lab`)
* **Learning Objective**: Analyze network traffic interception in unencrypted communications to understand passive sniffing risks.
* **MITRE ATT&CK**: 
  * *Tactic*: Collection (TA0009)
  * *Technique*: Adversary-in-the-Middle / Traffic Sniffing (T1557.001)
* **NIST CSF Function**: Detect (DE.CM-3: Personnel activity is monitored)
* **OWASP Top 10 (2021)**: A02:2021 - Cryptographic Failures
* **Vulnerable Component**: Plaintext HTTP service communicating across a bridged Docker network.
* **Tools Used**: `tcpdump`, `nc`, `curl`.
* **Checkpoints & Competency Levels**:
  * `CP01`: Capture unencrypted packets within the local lab network $\rightarrow$ *Level: Initial*
  * `CP02`: Extract sensitive plaintext credentials from packet payload $\rightarrow$ *Level: Autonomous*
* **Defensive Takeaway**: Mandating end-to-end encryption (TLS 1.3) across all network layers and eliminating plaintext protocols (HTTP, Telnet, FTP).
* **Controlled Simulation Note**: S05 is implemented as a controlled simulation of unencrypted traffic inspection within an isolated Docker bridge network. Active ARP spoofing is omitted to ensure pedagogical safety, platform stability, and deterministic reproducibility without violating host network policies.

---

## 3. Framework Coverage Summary Matrix

| Scenario | MITRE ATT&CK Tactic | NIST CSF Function | OWASP Top 10 (2021) | Primary Tools |
| :--- | :--- | :--- | :--- | :--- |
| **S01** | Reconnaissance | Identify / Protect | N/A (Infrastructure) | `nmap`, `ping`, `dig` |
| **S02** | Credential Access | Protect / Detect | A07: Authentication Failures | `curl`, `hydra` |
| **S03** | Initial Access / Execution | Protect | A03: Injection | `curl`, `grep` |
| **S04** | Credential Access | Protect / Detect | A07: Authentication Failures | `nmap`, `hydra`, `nc` |
| **S05** | Collection | Detect | A02: Cryptographic Failures | `tcpdump`, `nc` |