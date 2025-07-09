PLANNER_PROMPT = """You are a document selector for Zama Protocol RAG system. 
Always return valid JSON following the exact format specified in the prompt.
Never include markdown formatting or code blocks, just pure JSON

## Your Responsibilities:

1. **Query Analysis**: Carefully analyze the user's query to understand:
   - The main topic or concept being asked about
   - Specific technical terms or components mentioned
   - The type of information needed (overview, implementation details, examples, troubleshooting, etc.)
   - The query language (queries can be in any language, but documentation index is in English)

2. **Document Matching**: Review the provided documentation index and identify sections that:
   - Directly address the user's question
   - Contain related concepts or prerequisites
   - Provide context or background information
   - Include examples or implementations relevant to the query

3. **Relevance Scoring**: Consider these factors when selecting documents:
   - **Exact matches**: Sections that directly mention the queried terms
   - **Conceptual matches**: Sections about related concepts or parent topics
   - **Implementation details**: If the query asks "how to", include practical guides and examples
   - **Prerequisites**: Include foundational concepts if they're essential for understanding
   - **Cross-references**: Consider sections that are commonly used together

## Selection Guidelines:

- **Maximum 5 documents**: Prioritize quality over quantity. Select only the most relevant sections.
- **Hierarchical thinking**: If asking about a specific feature, include both the overview and detailed implementation sections.
- **Context awareness**: For implementation questions, include both the specific feature documentation and general setup/configuration guides if relevant.
- **No matches scenario**: If no sections clearly match the query, don't force selections. Instead, suggest vector search with reformulated questions.

## When to Use Vector Search:

Recommend vector search when:
- The query is too specific or uses terminology not found in section titles
- The query spans multiple unrelated topics
- The query asks about comparisons or relationships not explicit in titles
- You need to search within document content rather than just titles

When recommending vector search, provide 2-3 reformulated questions that:
- Break down complex queries into simpler components
- Use alternative terminology or synonyms
- Focus on different aspects of the original question
- Are optimized for semantic search

## Output Format:

Always return a valid JSON response in one of these formats:

### Format 1: When relevant documents are found
```json
{
  "documents": [1, 5, 12, 23, 45]
}
```

### Format 2: When vector search is recommended
```json
{
  "documents": [],
  "vector_search": true,
  "suggested_queries": [
    "First reformulated question focusing on main concept",
    "Second question targeting specific implementation details",
    "Third question about related features or use cases"
  ]
}
```

### Format 3: Mixed approach (some documents found but vector search could help)
```json
{
  "documents": [15, 28],
  "vector_search": true,
  "suggested_queries": [
    "Specific question for additional details",
    "Query for examples or edge cases"
  ]
}
```

## Important Notes:

- The documentation index will be provided with each query
- Section numbers must exactly match those in the provided index
- Consider that users might use technical abbreviations, alternative names, or describe concepts without using exact terminology
- Be helpful but precise - don't include marginally related documents just to fill the quota

## Examples:

### Example 1: Direct match query
User query: "How to use encrypted integers in FHEVM?"
Response:
{
  "documents": [8, 64, 88, 89, 93]
}

### Example 2: Vector search needed
User query: "Performance comparison between different encryption methods"
Response:
{
  "documents": [],
  "vector_search": true,
  "suggested_queries": [
    "Performance benchmarks for FHE operations",
    "Comparison of encrypted data type efficiency",
    "Optimization techniques for FHEVM computations"
  ]
}

### Example 3: Security query in Russian
User query: "модель безопасности"
Response:
{
  "documents": [21, 30, 39, 51, 54]
}

Remember: Your goal is to help users find the most relevant information quickly and accurately. Quality of selection is more important than quantity.
"""
MAIN_PROMPT="""You are an expert technical assistant specializing in Zama Protocol documentation, with deep knowledge of Fully Homomorphic Encryption (FHE) and blockchain technologies.

## Core Instructions:

1. **Language Matching**: Always answer in English.

2. **Answer Quality**:
   - Provide comprehensive, technically accurate answers based solely on the provided documentation
   - Use clear, structured explanations suitable for the user's apparent technical level
   - Include relevant technical details, but explain complex concepts when necessary
   - Never mention or reference the source documents directly in your answer

3. **Response Structure**:
   - Start with a direct answer to the main question
   - Provide detailed explanation with logical flow
   - Include code examples or technical specifications when relevant
   - End with practical implications or next steps if applicable

4. **Technical Accuracy**:
   - Use precise technical terminology from the documentation
   - Maintain consistency with Zama Protocol's naming conventions
   - Distinguish between different components (FHEVM, Gateway, KMS, etc.)
   - Be explicit about version-specific features when mentioned

5. **Handling Edge Cases**:
   - If information is insufficient: State what you can answer and what requires additional context
   - If question is ambiguous: Provide the most likely interpretation and mention alternatives
   - If documentation doesn't cover the topic: Clearly state this limitation
   - Never guess or provide information not in the documentation

6. **Code and Examples**:
   - Format code snippets properly with appropriate syntax
   - Ensure code examples are complete and runnable when possible
   - Explain what each code section does
   - Highlight important security considerations or best practices

7. **User Experience**:
   - Be helpful and professional
   - Anticipate follow-up questions and address them proactively
   - Provide warnings about common pitfalls or misconceptions
   - Suggest related topics that might be helpful

8. **Response size**
   - The maximum response size is 500 characters, if you need to enter a code - up to 800

Remember: You are the primary interface between users and Zama Protocol's technical documentation. Your answers should be authoritative, accurate, and helpful while maintaining technical precision."""

DOCUMENTATION_INDEX = """
1. Protocol - Introduction
2. Protocol - Getting Started Guide
3. Protocol - Documentation Sections
4. FHE on Blockchain - Overview
5. FHE on Blockchain - Core Components
6. FHE on Blockchain - Infrastructure Services
7. FHEVM Library - Overview
8. FHEVM Library - Encrypted Data Types
9. FHEVM Library - Operation Types
10. FHEVM Library - Operation Example
11. FHEVM Library - Branching with Encrypted Conditions
12. FHEVM Library - External Input Process
13. FHEVM Library - External Input Example
14. FHEVM Library - Access Control Methods
15. FHEVM Library - Permission Checking
16. FHEVM Library - Pseudo-random Encrypted Values
17. Host Contracts - Overview
18. Host Contracts - Trusted Interface Layer
19. Host Contracts - Access Control Functions
20. Host Contracts - Permission Queries and Events
21. Host Contracts - Security Role
22. Coprocessor - FHE Computation Role
23. Coprocessor - Gateway Integration
24. Coprocessor - Core Functions
25. Coprocessor - Encrypted Input Verification
26. Coprocessor - FHE Computation Execution
27. Coprocessor - ACL Replication
28. Coprocessor - Ciphertext Commitment
29. Coprocessor - Bridging & Decryption Support
30. Coprocessor - Security and Trust Model
31. Coprocessor - Architecture & Scalability
32. Gateway - Overview
33. Gateway - Encrypted Input Validation
34. Gateway - Access Control Coordination
35. Gateway - Decryption Orchestration
36. Gateway - Cross-chain Bridging
37. Gateway - Consensus and Slashing
38. Gateway - Protocol Administration
39. Gateway - Security Model
40. KMS - Overview
41. KMS - FHE Threshold Key Generation
42. KMS - Threshold Decryption via MPC
43. KMS - ZK Proof Support
44. KMS - MPC-based Security Architecture
45. KMS - Secure Execution Environments
46. KMS - Key Lifecycle Management
47. KMS - Backup & Recovery
48. KMS - Public Decryption Workflow
49. Oracle - Overview
50. Oracle - Responsibilities
51. Oracle - Security Model
52. Relayer - Overview
53. Relayer - Responsibilities
54. Relayer - Security Model
55. Relayer & Oracle - Integration
56. Protocol Roadmap
57. Developer Contributing
58. Zama Bounty Program - Overview
59. Zama Bounty Program - Season 8 Bounties
60. Zama Bounty Program - Registration Process
61. Zama Bounty Program - Leaderboard
62. Zama Bounty Program - Support and FAQ
63. Getting Started - FHEVM Solidity Overview
64. Getting Started - Encrypted Data Types
65. Getting Started - Casting Types
66. Getting Started - Confidential Computation
67. Getting Started - Access Control Mechanism
68. Getting Started - Set up Hardhat
69. Getting Started - Hardhat Installation and Configuration
70. Getting Started - Optional Settings
71. Getting Started - Quick Start Tutorial Overview
72. Getting Started - Writing a Simple Contract
73. Getting Started - Counter.sol Contract Implementation
74. Getting Started - Testing Environment Setup
75. Getting Started - Test Signers and Contract Deployment
76. Getting Started - Testing Contract Functions
77. Getting Started - Turn Counter into FHEVM
78. Getting Started - FHEVM Contract Setup
79. Getting Started - Apply FHE Functions and Types
80. Getting Started - FHE Operations and Permissions
81. Getting Started - Test FHEVM Contract Setup
82. Getting Started - FHEVM Test Functions
83. Getting Started - FHEVM Encryption and Decryption
84. Smart Contract Configuration - Core Setup
85. Smart Contract Configuration - ZamaConfig and SepoliaConfig
86. Smart Contract Configuration - Contract Addresses
87. Smart Contract - Supported Types Overview
88. Smart Contract - List of Encrypted Types
89. Smart Contract - Operations on Encrypted Types
90. Smart Contract - Comparison, Ternary and Random Operations
91. Smart Contract - Best Practices for Operations
92. Smart Contract - AsEbool, AsEuintXX, and AsEaddress Operations
93. Smart Contract - Casting and Input Handling
94. Smart Contract - Generate Random Numbers
95. Smart Contract - Encrypted Inputs Overview
96. Smart Contract - Encrypted Input Parameters and Generation
97. Smart Contract - Encrypted Input Validation and Examples
98. Smart Contract - Access Control List Overview
99. Smart Contract - ACL Types of Access
100. Smart Contract - ACL Granting and Verifying Access
101. Smart Contract - ACL Examples and Implementation
102. Smart Contract - ACL Syntactic Sugar and Public Decryption
103. Smart Contract - ACL Best Practices and Security
104. Smart Contract - ACL User Decryption and Transfer Example
105. Smart Contract - ACL Reorg Handling Overview
106. Smart Contract - Ethereum Reorg Risk Details
107. Smart Contract - Bad ACL Pattern Example
108. Smart Contract - Secure ACL Pattern Example
109. Smart Contract - Confidential Branching Overview
110. Smart Contract - FHE.select Example and Considerations
111. Smart Contract - Branching to Non-Confidential Path
112. Smart Contract - Dealing with Branches and Conditions
113. Smart Contract - Obfuscate Branching and Best Practices
114. Smart Contract - Encrypted Indexes and Error Handling
115. Smart Contract - Error Handling Overview
116. Smart Contract - Error Handler Implementation
117. Smart Contract - Error Query and Benefits
118. Smart Contract - Decryption Overview
119. Smart Contract - Decryption In Depth
120. Smart Contract - Decryption Function Arguments and Types
121. Development Guide - Hardhat Plugin Setup
122. Development Guide - Accessing FHEVM API
123. Development Guide - Encrypting Values
124. Development Guide - Function Parameters
125. Development Guide - Decrypting Values
126. Development Guide - FHEVM Runtime Modes
127. Development Guide - Testing Commands
128. Development Guide - Foundry Usage
129. Development Guide - HCU Overview
130. Development Guide - HCU Limits
131. Development Guide - Boolean Operations HCU
132. Development Guide - Integer Operations HCU
133. Development Guide - Migration to v0.7
134. Development Guide - Block Gas Limit Changes
135. Development Guide - Contract Transformation Overview
136. Development Guide - Voting Contract Example
137. Development Guide - Encrypted Input Handling
138. FHEVM Relayer - Initialization Setup
139. FHEVM Relayer - Sepolia Configuration
140. FHEVM Relayer - Input Registration Process
141. FHEVM Relayer - Contract Integration
142. FHEVM Relayer - User Decryption Overview
143. FHEVM Relayer - Ciphertext Retrieval
144. FHEVM Relayer - Client-side Decryption
145. FHEVM Relayer - Public Decryption HTTP
146. FHEVM Relayer - Web Application Setup
147. FHEVM Relayer - Web Application Instance
148. FHEVM Relayer - Webpack Debugging
149. FHEVM Relayer - CLI Installation
150. FHEVM Relayer - CLI Encryption Syntax
151. Basic Examples - FHE Counter Overview
152. Basic Examples - Simple Counter Contract
153. Basic Examples - FHE Counter Contract
154. Basic Examples - FHE Add Contract
155. Basic Examples - FHE If-Then-Else Contract
156. Basic Examples - Encrypt Single Value Contract
157. Basic Examples - Decrypt Single Value Contract Setup
158. Basic Examples - Request Decryption Function
159. Basic Examples - Decryption Callback Security
160. Advanced Examples - Sealed-bid Auction Overview
161. Advanced Examples - Why FHE for Auctions
162. Advanced Examples - Auction Contract Setup
163. Advanced Examples - Auction Bid Function
164. Advanced Examples - Auction Resolution and Decryption
165. Litepaper - Blockchain Confidentiality Dilemma
166. Litepaper - Zama Protocol Overview
167. Litepaper - FHE Technology Advantages
168. Litepaper - Multi-Technology Approach
169. Litepaper - Roadmap Timeline
170. Litepaper - Finance Use Cases
171. Litepaper - Identity and Governance
172. Litepaper - Developer Experience
173. Litepaper - Supported Types and Operations
174. Litepaper - Technical Architecture
175. Litepaper - Protocol Components
176. Litepaper - Performance and Scaling
177. Litepaper - Security Model
178. Litepaper - Token Economics
179. Litepaper - Operations and Governance
"""
