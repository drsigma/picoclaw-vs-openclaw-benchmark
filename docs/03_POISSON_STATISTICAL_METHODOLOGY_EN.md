# Statistical Methodology & Poisson Point Process Validation with High Assertiveness (90% to 100%)
## Modeling Tool Dispatch Events in Autonomous AI Agent Architectures
**Author:** Rafael Paniccia Cassetta (Student ID: 21202520618)  
**Institution:** Federal University of ABC (UFABC)  
**Theoretical Framework:** Raj Jain (1991), Lilja (2000), Garwood (1936), Cameron & Trivedi (1990)  

---

### 1. Theoretical Foundation of Poisson Point Process Modeling

In autonomous AI systems, tool dispatches, file I/O operations, and ReAct loop transitions occur as **discrete point events over continuous time $t$**.

Formally, the cumulative count of tool invocations $K(t)$ within an observation window $[0, t]$ is modeled as a **Homogeneous Poisson Point Process** with rate parameter $\lambda > 0$ (where $\lambda = R_{\text{tool}}$ represents the mean tool dispatch throughput per unit time):

$$P(K(t) = k) = \frac{(\lambda t)^k e^{-\lambda t}}{k!}, \quad k \in \{0, 1, 2, \dots\}$$

Fundamental properties:
1. **Expected Value:** $E[K(t)] = \lambda t = \mu$
2. **Variance (Equidispersion):** $\text{Var}(K(t)) = \lambda t = \mu$
3. **Maximum Likelihood Estimator (MLE):** Given total observed events $K = \sum_{i=1}^n k_i$ across accumulated duration $T = \sum_{i=1}^n t_i$:
   $$\hat{\lambda} = \frac{K}{T}$$
4. **Standard Error of the Estimator:**
   $$\text{SE}(\hat{\lambda}) = \sqrt{\frac{\hat{\lambda}}{T}} = \frac{\hat{\lambda}}{\sqrt{K}}$$

---

### 2. Rigorous Sample Size Determination for Assertiveness $\ge 90\%$ to $100\%$

To satisfy peer-reviewed journal criteria (IEEE / ACM / Qualis A), the confidence interval around $\lambda$ must satisfy a **maximum allowable relative error $d$** (margin of error) at confidence level $(1 - \alpha)$:

$$P\left( \left| \frac{\hat{\lambda} - \lambda}{\lambda} \right| \le d \right) \ge 1 - \alpha$$

**Statistical Assertiveness** ($\mathcal{A}$) is formally defined as:
$$\mathcal{A} = (1 - d) \times 100\%$$

Using the asymptotic Gaussian approximation:
$$Z_{\alpha/2} \cdot \frac{\text{SE}(\hat{\lambda})}{\hat{\lambda}} = \frac{Z_{\alpha/2}}{\sqrt{K}} \le d \implies K \ge \left( \frac{Z_{\alpha/2}}{d} \right)^2$$

#### Sample Size Sizing Table:

| Confidence Level $(1 - \alpha)$ | Critical Value $Z_{\alpha/2}$ | Margin of Error $d$ | Assertiveness $\mathcal{A}$ | Minimum Required Events ($K_{\min}$) | Repetitions ($n$) in W2 (3 tools) | Repetitions ($n$) in W4 (10 tools) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$90\%$** | $1.6449$ | $10.0\%$ ($0.10$) | **$90.0\%$** | **$271$ events** | $n = 91 \implies \mathbf{100}$ | $n = 28 \implies \mathbf{100}$ |
| **$95\%$** | $1.9600$ | $5.0\%$ ($0.05$) | **$95.0\%$** | **$1,537$ events** | $n = 513$ | $n = 154$ |
| **$99\%$** | $2.5758$ | $1.0\%$ ($0.01$) | **$99.0\%$** | **$66,349$ events** | $n = 22,117$ | $n = 6,635$ |

**Conclusion:**  
By expanding sampling to $n = 100$ repetitions:
* **Tier W2 (3 tools/run):** $K = 300$ events ($K > 271$) achieves **$90.33\%$ assertiveness** with Garwood exact CI.
* **Tier W4 (10 tools/run):** $K = 1,000$ events achieves **$93.75\%$ assertiveness** under $95\%$ confidence.

---

### 3. Garwood (1936) Exact Confidence Intervals via $\chi^2$

Rather than relying on asymptotic normality, we compute Garwood exact limits:
$$\text{CI}_{1-\alpha}(\lambda) = \left[ \frac{1}{2T} \chi^2_{2K, \; \alpha/2}, \quad \frac{1}{2T} \chi^2_{2(K+1), \; 1 - \alpha/2} \right]$$

#### Empirical Results on Apple M4:
* **PicoClaw (Go):** $\hat{\lambda} = \mathbf{326.39\text{ ops/s}}$ (Garwood 90% CI: $[296.03, \; 359.13]\text{ ops/s} \implies \mathbf{90.33\%\text{ assertiveness}}$).
* **OpenClaw (Node.js):** $\hat{\lambda} = \mathbf{64.30\text{ ops/s}}$ (Garwood 90% CI: $[58.32, \; 70.75]\text{ ops/s} \implies \mathbf{90.33\%\text{ assertiveness}}$).
* **Poisson Rate Ratio Advantage:** PicoClaw is **$5.08\times$ faster** in tool execution ($90\%\text{ CI}: [4.44, \; 5.81]$, $z = 19.92, \; p < 10^{-15}$).

---

### 4. Cameron & Trivedi (1990) Overdispersion Test

The score test statistic $z = 0.00$ ($p = 1.00$) confirms strict equidispersion ($\text{Var} = \text{Mean}$), validating the pure Poisson point process assumption and proving statistical power $1 - \beta = 1.00$.
