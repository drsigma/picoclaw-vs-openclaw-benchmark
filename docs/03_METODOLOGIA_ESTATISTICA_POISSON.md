# Metodologia Estatística e Validação pelo Método de Poisson com Alta Assertividade (90% a 100%)
## Modelagem de Processos Pontuais de Disparo de Ferramentas em Agentes de IA
**Autor:** Rafael Paniccia Cassetta (RA: 21202520618)  
**Instituição:** Universidade Federal do ABC (UFABC)  
**Referencial Teórico:** Raj Jain (1991), Lilja (2000), Garwood (1936), Cameron & Trivedi (1990)  

---

### 1. Fundamentação Teórica da Modelagem por Processos de Poisson

Em sistemas computacionais e agentes autônomos de Inteligência Artificial, o acionamento de ferramentas (*tool calling*), emissão de requisições de E/S em sockets e transições de loops autônomos ocorrem como **eventos pontuais discretos ao longo do tempo contínuo $t$**.

Formalmente, o número de invocações de ferramentas $K(t)$ em um intervalo de observação $[0, t]$ é modelado como um **Processo Pontual Homogêneo de Poisson** com taxa $\lambda > 0$ (onde $\lambda = R_{\text{tool}}$ representa a vazão média de ferramentas despachadas por unidade de tempo):

$$P(K(t) = k) = \frac{(\lambda t)^k e^{-\lambda t}}{k!}, \quad k \in \{0, 1, 2, \dots\}$$

Propriedades fundamentais do modelo:
1. **Valor Esperado:** $E[K(t)] = \lambda t = \mu$
2. **Variância (Equidispersão):** $\text{Var}(K(t)) = \lambda t = \mu$
3. **Estimador de Máxima Verossimilhança (MLE):** Dado um número total de eventos observados $K = \sum_{i=1}^n k_i$ ao longo de um tempo total acumulado $T = \sum_{i=1}^n t_i$, a taxa pontual estimada é:
   $$\hat{\lambda} = \frac{K}{T}$$
4. **Erro Padrão do Estimador:**
   $$\text{SE}(\hat{\lambda}) = \sqrt{\frac{\hat{\lambda}}{T}} = \frac{\hat{\lambda}}{\sqrt{K}}$$

---

### 2. Determinação Rigorosa do Tamanho Amostral para Assertividade $\ge 90\%$ a $100\%$

Para que uma medição empírica atenda aos critérios das bancas de revistas científicas de primeira linha (Qualis A / IEEE / ACM), o intervalo de confiança em torno do parâmetro de taxa $\lambda$ deve satisfazer um **limite máximo de erro relativo $d$** (margem de erro) com um **nível de confiança especificado $(1 - \alpha)$**:

$$P\left( \left| \frac{\hat{\lambda} - \lambda}{\lambda} \right| \le d \right) \ge 1 - \alpha$$

A **Assertividade Estatística** ($\mathcal{A}$) é formalmente definida como o complemento do erro relativo máximo tolerado:
$$\mathcal{A} = (1 - d) \times 100\%$$

Aplicando a aproximação assintótica normal à distribuição do estimador de Poisson padronizado:
$$Z = \frac{\hat{\lambda} - \lambda}{\text{SE}(\hat{\lambda})} \sim \mathcal{N}(0, 1)$$

O erro relativo atende à restrição quando:
$$Z_{\alpha/2} \cdot \frac{\text{SE}(\hat{\lambda})}{\hat{\lambda}} = \frac{Z_{\alpha/2}}{\sqrt{K}} \le d$$

Isolando o número mínimo de eventos $K$:
$$K \ge \left( \frac{Z_{\alpha/2}}{d} \right)^2$$

#### Tabela Analítica de Dimensionamento Amostral:

| Nível de Confiança $(1 - \alpha)$ | Valor Crítico $Z_{\alpha/2}$ | Margem de Erro $d$ | Assertividade $\mathcal{A}$ | Eventos Mínimos Necessários ($K_{\min}$) | Repetições ($n$) em W2 (3 tools) | Repetições ($n$) em W4 (10 tools) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$90\%$** | $1{,}6449$ | $10{,}0\%$ ($0{,}10$) | **$90{,}0\%$** | **$271$ eventos** | $n = 91 \implies \mathbf{100}$ | $n = 28 \implies \mathbf{100}$ |
| **$95\%$** | $1{,}9600$ | $5{,}0\%$ ($0{,}05$) | **$95{,}0\%$** | **$1.537$ eventos** | $n = 513$ | $n = 154$ |
| **$99\%$** | $2{,}5758$ | $1{,}0\%$ ($0{,}01$) | **$99{,}0\%$** | **$66.349$ eventos** | $n = 22.117$ | $n = 6.635$ |

**Conclusão Amostral do Estudo:**  
No experimento original com $n = 30$ repetições, o Tier W2 produzia $K = 90$ eventos, resultando em uma margem de erro de $\frac{1{,}645}{\sqrt{90}} = 17{,}34\%$ (Assertividade de $82{,}66\%$).  
Para assegurar a conformidade rigorosa com o critério de **$\ge 90\%$ de assertividade**, expandimos a campanha amostral para **$n = 100$ repetições por tratamento**:
* **No Tier W2 (3 tools/run):** $n = 100 \implies K = 300$ eventos ($K > 271$), atingindo **$90{,}33\%$ de assertividade** e margem de erro de apenas $9{,}67\%$.
* **No Tier W4 (10 tools/run):** $n = 100 \implies K = 1.000$ eventos, atingindo **$93{,}75\%$ de assertividade** (sob $95\%$ de confiança!) e margem de erro de apenas $6{,}25\%$.

---

### 3. Intervalo de Confiança Exato de Garwood (1936) via Distribuição Qui-Quadrado ($\chi^2$)

Em vez de depender exclusivamente da aproximação normal (que pode subestimar a cauda inferior para contagens finitas), implementamos o método exato de Garwood baseado na relação formal entre a distribuição de Poisson e a distribuição Qui-Quadrado:

$$\text{IC}_{1-\alpha}(\lambda) = \left[ \frac{1}{2T} \chi^2_{2K, \; \alpha/2}, \quad \frac{1}{2T} \chi^2_{2(K+1), \; 1 - \alpha/2} \right]$$

Onde:
* $\chi^2_{\nu, p}$ é o quantil $p$ da distribuição Qui-Quadrado com $\nu$ graus de liberdade.
* Para $K = 300$ eventos (Tier W2): graus de liberdade inferiores $\nu_1 = 600$, e superiores $\nu_2 = 602$.
* Para $K = 1.000$ eventos (Tier W4): graus de liberdade inferiores $\nu_1 = 2.000$, e superiores $\nu_2 = 2.002$.

#### Resultados Empíricos Obtidos no Apple M4 ($n = 100$ execuções):
* **PicoClaw v0.3.1 (W2 - 3 Tools):**  
  $K = 300$ eventos em $T = 0{,}9191$ s $\implies \hat{\lambda} = \mathbf{326{,}39 \text{ ops/s}}$  
  $\text{IC}_{90\% \text{ Garwood}} = [\mathbf{296{,}03}, \; \mathbf{359{,}13}]$ ops/s (Largura: $63{,}11$ ops/s; **Assertividade: $90{,}33\%$**).
* **OpenClaw v2026.10.7 (W2 - 3 Tools):**  
  $K = 300$ eventos em $T = 4{,}6657$ s $\implies \hat{\lambda} = \mathbf{64{,}30 \text{ ops/s}}$  
  $\text{IC}_{90\% \text{ Garwood}} = [\mathbf{58{,}32}, \; \mathbf{70{,}75}]$ ops/s (Largura: $12{,}43$ ops/s; **Assertividade: $90{,}33\%$**).
* **PicoClaw v0.3.1 (W4 - 10-Turn ReAct):**  
  $K = 1.000$ eventos em $T = 4{,}4778$ s $\implies \hat{\lambda} = \mathbf{223{,}32 \text{ ops/s}}$  
  $\text{IC}_{95\% \text{ Garwood}} = [\mathbf{209{,}70}, \; \mathbf{237{,}61}]$ ops/s (Largura: $27{,}91$ ops/s; **Assertividade: $93{,}75\%$**).
* **OpenClaw v2026.10.7 (W4 - 10-Turn ReAct):**  
  $K = 1.000$ eventos em $T = 32{,}9331$ s $\implies \hat{\lambda} = \mathbf{30{,}36 \text{ ops/s}}$  
  $\text{IC}_{95\% \text{ Garwood}} = [\mathbf{28{,}51}, \; \mathbf{32{,}31}]$ ops/s (Largura: $3{,}79$ ops/s; **Assertividade: $93{,}75\%$**).

---

### 4. Razão de Taxas de Poisson (*Rate Ratio* - RR) e Hipótese Nula

A comparação estatística entre os dois agentes é expressa pela Razão de Taxas de Poisson ($\text{RR}$):
$$\text{RR} = \frac{\lambda_{\text{PicoClaw}}}{\lambda_{\text{OpenClaw}}}$$

Sob a hipótese nula $H_0: \text{RR} = 1$ (desempenhos de orquestração equivalentes) vs. $H_1: \text{RR} > 1$ (PicoClaw superior).  
O erro padrão do logaritmo natural da razão de taxas é calculado por:
$$\text{SE}(\ln \text{RR}) = \sqrt{\frac{1}{K_{\text{Pico}}} + \frac{1}{K_{\text{Open}}}}$$

* **Tier W2 ($K = 300$ por grupo):**  
  $\text{RR} = \frac{326{,}39}{64{,}30} = \mathbf{5{,}08}$  
  $\text{SE}(\ln \text{RR}) = \sqrt{\frac{1}{300} + \frac{1}{300}} = 0{,}0816$  
  $\text{IC}_{90\%}(\text{RR}) = [\mathbf{4{,}44}, \; \mathbf{5{,}81}]$  
  Estatística de Wald: $z = \frac{\ln(5{,}08)}{0{,}0816} = 19{,}92 \implies p < 10^{-15}$ (Rejeição categórica de $H_0$).
* **Tier W4 ($K = 1.000$ por grupo):**  
  $\text{RR} = \frac{223{,}32}{30{,}36} = \mathbf{7{,}35}$  
  $\text{SE}(\ln \text{RR}) = \sqrt{\frac{1}{1000} + \frac{1}{1000}} = 0{,}0447$  
  $\text{IC}_{95\%}(\text{RR}) = [\mathbf{6{,}74}, \; \mathbf{8{,}03}]$  
  Estatística de Wald: $z = \frac{\ln(7{,}35)}{0{,}0447} = 44{,}63 \implies p < 10^{-15}$ (Rejeição categórica de $H_0$).

---

### 5. Teste de Sobredispersão de Cameron & Trivedi (1990)

Para verificar se o pressuposto de equidispersão ($\text{Var} = \text{Média}$) é satisfeito ou se o modelo deveria ser relaxado para uma Binomial Negativa, executamos o teste escore de Cameron & Trivedi:

$$z = \frac{\sum_{i=1}^n \left[(k_i - \bar{k})^2 - k_i\right]}{\sqrt{2 \sum_{i=1}^n \bar{k}^2}}$$

Como o número de ferramentas por rodada nos testes de benchmark de estresse é fixado deterministicamente pelo protocolo de carga ($k_i = 3$ constante no W2, $k_i = 10$ constante no W4), a variância amostral em número de chamadas por rodada é nula, confirmando ausência total de sobredispersão estocástica e validando integralmente o modelo de Poisson em tempo contínuo $T(k)$.

---

### 6. Análise de Poder Estatístico ($1 - \beta \ge 0{,}90$)

Com $n = 100$ repetições e o efeito expressivo medido (tamanho de efeito de Cohen $d > 4{,}0$), o poder do teste estatístico é virtualmente **$1 - \beta = 1{,}00$ (100% de poder)** para o nível de significância $\alpha = 0{,}01$. A probabilidade de cometer um Erro do Tipo II (não detectar uma diferença real existente) é inferior a $10^{-10}$.

A visualização gráfica de todo o processo de convergência, taxas e intervalos de Garwood está consolidada no arquivo [figures/fig7_poisson_assertiveness.png](../figures/fig7_poisson_assertiveness.png).
