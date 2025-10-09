-- Seed Data: Module 1 Lessons (1-15)
-- Trading Fundamentals
-- Phase 2: Educational Content

-- ============================================
-- LESSON 1: What is Trading?
-- ============================================

INSERT INTO lessons (lesson_number, module_number, title, description, content, estimated_duration, xp_reward, difficulty, prerequisites, tags)
VALUES (
    1,
    1,
    'What is Trading?',
    'Learn the fundamental differences between trading and investing, explore various market types, and understand how exchanges work.',
    '{
        "sections": [
            {
                "type": "text",
                "content": "# What is Trading?\n\n## Introduction\n\nWelcome to your first lesson! Trading is the act of buying and selling financial assets with the goal of making a profit. Unlike long-term investing, trading typically involves shorter time horizons and more frequent transactions.\n\n## Trading vs. Investing\n\n**Trading:**\n- Short to medium-term focus (minutes to months)\n- More frequent buying and selling\n- Seeks to profit from price movements\n- Requires active monitoring\n- Higher risk, potentially higher returns\n\n**Investing:**\n- Long-term focus (years to decades)\n- Buy and hold strategy\n- Seeks gradual wealth accumulation\n- Less active monitoring required\n- Generally lower risk\n\n## Types of Markets\n\n### 1. Stock Market\nTrade shares of publicly-traded companies like Apple, Microsoft, and Tesla.\n\n### 2. Forex Market\nTrade currencies like USD/EUR, GBP/JPY. Open 24 hours, 5 days a week.\n\n### 3. Cryptocurrency Market\nTrade digital assets like Bitcoin, Ethereum. Open 24/7.\n\n### 4. Commodities Market\nTrade physical goods like gold, oil, wheat.\n\n### 5. Bonds Market\nTrade debt instruments issued by governments and corporations.\n\n## How Exchanges Work\n\nExchanges are marketplaces where buyers and sellers meet:\n\n1. **Order Matching:** Buy orders are matched with sell orders\n2. **Price Discovery:** Supply and demand determine prices\n3. **Transparency:** All trades are recorded and visible\n4. **Regulation:** Exchanges ensure fair trading practices\n\nPopular exchanges:\n- **NYSE** (New York Stock Exchange) - Stocks\n- **NASDAQ** - Technology stocks\n- **Euronext Brussels** - European stocks (including Belgian stocks)\n- **Coinbase** - Cryptocurrency\n\n## Key Takeaways\n\n✅ Trading focuses on short-term profit from price movements\n\n✅ Multiple markets exist: stocks, forex, crypto, commodities\n\n✅ Exchanges provide secure, regulated platforms for trading\n\n✅ Understanding the basics is crucial before starting"
            }
        ]
    }'::jsonb,
    15,
    100,
    'beginner',
    '[]'::jsonb,
    '["fundamentals", "basics", "introduction"]'::jsonb
);

-- Quiz for Lesson 1
INSERT INTO quizzes (lesson_id, questions, passing_score)
VALUES (
    (SELECT lesson_id FROM lessons WHERE lesson_number = 1),
    '[
        {
            "question": "What is the main difference between trading and investing?",
            "type": "multiple_choice",
            "options": [
                "Trading is short-term, investing is long-term",
                "Trading is safer than investing",
                "Investing requires more money",
                "There is no difference"
            ],
            "correct_answer": 0,
            "explanation": "Trading typically focuses on short to medium-term gains through frequent transactions, while investing is a long-term strategy focused on gradual wealth accumulation."
        },
        {
            "question": "Which market is open 24/7?",
            "type": "multiple_choice",
            "options": [
                "Stock market",
                "Cryptocurrency market",
                "Bond market",
                "Commodity market"
            ],
            "correct_answer": 1,
            "explanation": "The cryptocurrency market operates 24 hours a day, 7 days a week, unlike traditional markets that have set trading hours."
        },
        {
            "question": "What is an exchange?",
            "type": "multiple_choice",
            "options": [
                "A type of investment",
                "A marketplace where buyers and sellers trade assets",
                "A government agency",
                "A cryptocurrency"
            ],
            "correct_answer": 1,
            "explanation": "An exchange is a regulated marketplace that facilitates trading by matching buy and sell orders between market participants."
        },
        {
            "question": "Trading requires more active monitoring than long-term investing.",
            "type": "true_false",
            "correct_answer": true,
            "explanation": "True. Trading involves shorter time frames and more frequent transactions, requiring traders to actively monitor markets and positions."
        },
        {
            "question": "Which exchange is primarily focused on technology stocks?",
            "type": "multiple_choice",
            "options": [
                "NYSE",
                "NASDAQ",
                "Euronext",
                "LSE"
            ],
            "correct_answer": 1,
            "explanation": "NASDAQ is known for listing many technology companies like Apple, Microsoft, Amazon, and Google."
        }
    ]'::jsonb,
    70
);


-- ============================================
-- LESSON 2: Market Participants
-- ============================================

INSERT INTO lessons (lesson_number, module_number, title, description, content, estimated_duration, xp_reward, difficulty, prerequisites, tags)
VALUES (
    2,
    1,
    'Market Participants',
    'Understand who trades in the markets: retail traders, institutional investors, market makers, and regulators.',
    '{
        "sections": [
            {
                "type": "text",
                "content": "# Market Participants\n\n## Who Trades in the Markets?\n\nFinancial markets consist of various participants, each with different roles, goals, and resources. Understanding who they are helps you navigate the market landscape.\n\n## 1. Retail Traders (Individual Investors)\n\n**Who they are:**\n- Individual people like you and me\n- Trade with personal accounts\n- Typically smaller capital\n\n**Characteristics:**\n- Use online brokers (like Bolero, Robinhood, eToro)\n- Trade from home or mobile apps\n- May trade part-time or full-time\n- Access to same markets as institutions\n\n**Advantages:**\n- Flexible trading schedule\n- No client obligations\n- Can act quickly on opportunities\n\n**Challenges:**\n- Limited capital compared to institutions\n- Less access to research and tools\n- Higher relative costs (commissions)\n\n## 2. Institutional Investors\n\n**Who they are:**\n- Banks, hedge funds, pension funds\n- Mutual funds and ETFs\n- Insurance companies\n\n**Characteristics:**\n- Trade with millions or billions\n- Professional teams of analysts\n- Advanced technology and data\n- Move markets with large orders\n\n**Examples:**\n- BlackRock (world''s largest asset manager)\n- Vanguard (index funds)\n- JP Morgan (investment bank)\n\n## 3. Market Makers\n\n**Role:**\nProvide liquidity by always being ready to buy or sell.\n\n**How they work:**\n- Quote both bid (buy) and ask (sell) prices\n- Profit from the spread (difference between bid and ask)\n- Keep markets functioning smoothly\n\n**Example:**\nMarket maker for Apple stock:\n- Bid: $150.00 (willing to buy)\n- Ask: $150.05 (willing to sell)\n- Spread: $0.05 profit per share\n\n## 4. Brokers\n\n**Role:**\nFacilitate trades between buyers and sellers.\n\n**Types:**\n- **Full-service brokers:** Provide advice, research, planning\n- **Discount brokers:** Execute trades cheaply, minimal advice\n- **Online brokers:** Self-service platforms (Bolero, Interactive Brokers)\n\n**How they make money:**\n- Commissions on trades\n- Spreads on certain assets\n- Account fees\n- Payment for order flow (PFOF)\n\n## 5. Regulators\n\n**Role:**\nEnsure fair, transparent, and orderly markets.\n\n**Major regulators:**\n- **SEC** (USA) - Securities and Exchange Commission\n- **ESMA** (EU) - European Securities and Markets Authority\n- **FSMA** (Belgium) - Financial Services and Markets Authority\n\n**What they do:**\n- Prevent fraud and manipulation\n- Enforce disclosure rules\n- Protect investors\n- Investigate violations\n\n## Market Dynamics\n\nAll participants interact:\n\n1. **Retail trader** places order through **broker**\n2. **Broker** routes order to **exchange**\n3. **Market maker** provides liquidity\n4. **Institutional investors** create price movements\n5. **Regulators** oversee everything\n\n## Key Takeaways\n\n✅ Retail traders compete alongside large institutions\n\n✅ Market makers provide liquidity and keep markets functioning\n\n✅ Brokers are intermediaries that execute your trades\n\n✅ Regulators protect investors and ensure fair markets\n\n✅ Understanding participants helps you understand market behavior"
            }
        ]
    }'::jsonb,
    15,
    100,
    'beginner',
    '[1]'::jsonb,
    '["fundamentals", "market-structure", "participants"]'::jsonb
);

-- Quiz for Lesson 2
INSERT INTO quizzes (lesson_id, questions, passing_score)
VALUES (
    (SELECT lesson_id FROM lessons WHERE lesson_number = 2),
    '[
        {
            "question": "What is the primary role of market makers?",
            "type": "multiple_choice",
            "options": [
                "To provide investment advice",
                "To provide liquidity by quoting bid and ask prices",
                "To regulate the markets",
                "To manage pension funds"
            ],
            "correct_answer": 1,
            "explanation": "Market makers provide liquidity by continuously quoting prices at which they will buy (bid) and sell (ask), earning the spread between these prices."
        },
        {
            "question": "What is a broker?",
            "type": "multiple_choice",
            "options": [
                "Someone who provides market liquidity",
                "A government regulator",
                "An intermediary who facilitates trades",
                "A long-term investor"
            ],
            "correct_answer": 2,
            "explanation": "A broker acts as an intermediary between buyers and sellers, executing trades on behalf of clients."
        },
        {
            "question": "Institutional investors typically trade with larger capital than retail traders.",
            "type": "true_false",
            "correct_answer": true,
            "explanation": "True. Institutional investors like banks, hedge funds, and pension funds manage millions or billions in assets, far more than typical retail traders."
        },
        {
            "question": "Which organization regulates financial markets in Belgium?",
            "type": "multiple_choice",
            "options": [
                "SEC",
                "ESMA",
                "FSMA",
                "FCA"
            ],
            "correct_answer": 2,
            "explanation": "FSMA (Financial Services and Markets Authority) is the Belgian regulator responsible for overseeing financial markets and protecting investors."
        },
        {
            "question": "Market makers profit from:",
            "type": "multiple_choice",
            "options": [
                "Long-term price appreciation",
                "The spread between bid and ask prices",
                "Commission fees",
                "Dividend payments"
            ],
            "correct_answer": 1,
            "explanation": "Market makers profit from the spread - the small difference between the price they''re willing to buy at (bid) and the price they''re willing to sell at (ask)."
        }
    ]'::jsonb,
    70
);


-- ============================================
-- LESSON 3: Understanding Stocks
-- ============================================

INSERT INTO lessons (lesson_number, module_number, title, description, content, estimated_duration, xp_reward, difficulty, prerequisites, tags)
VALUES (
    3,
    1,
    'Understanding Stocks',
    'Learn what stocks are, how they represent ownership in companies, and the difference between common and preferred shares.',
    '{
        "sections": [
            {
                "type": "text",
                "content": "# Understanding Stocks\n\n## What is a Stock?\n\nA **stock** (also called a share or equity) represents partial ownership in a company. When you buy stock, you become a shareholder and own a small piece of that business.\n\n## Why Do Companies Issue Stock?\n\nCompanies sell stock to:\n1. **Raise Capital:** Fund expansion, research, or operations\n2. **Go Public:** Transition from private to public ownership (IPO)\n3. **Provide Liquidity:** Allow founders and early investors to cash out\n4. **Currency for Acquisitions:** Use stock to buy other companies\n\n## Stock Ownership Rights\n\nAs a shareholder, you typically have:\n\n### 1. Voting Rights\n- Vote on major company decisions\n- Elect board of directors\n- Approve mergers and acquisitions\n- Usually 1 share = 1 vote\n\n### 2. Dividend Rights\n- Receive portion of company profits\n- Paid quarterly, annually, or not at all\n- Example: If you own 100 shares and dividend is $1/share, you receive $100\n\n### 3. Residual Claims\n- If company is liquidated, shareholders get what''s left after debts are paid\n- Common shareholders are last in line\n\n## Common Stock vs. Preferred Stock\n\n### Common Stock\n\n**Characteristics:**\n- Standard stock that most people buy\n- Voting rights included\n- Variable dividends (can increase, decrease, or stop)\n- Higher growth potential\n- Higher risk\n\n**Example:**\nApple (AAPL), Microsoft (MSFT), Tesla (TSLA)\n\n### Preferred Stock\n\n**Characteristics:**\n- Fixed dividend payments (like bonds)\n- Priority over common stock for dividends\n- Priority in bankruptcy/liquidation\n- Usually no voting rights\n- Lower growth potential\n- Lower risk than common stock\n\n**Example:**\nBank of America Preferred Series (BAC.PR.B)\n\n### Comparison Table\n\n| Feature | Common Stock | Preferred Stock |\n|---------|-------------|----------------|\n| Voting Rights | ✅ Yes | ❌ Usually No |\n| Dividends | Variable | Fixed |\n| Growth Potential | High | Lower |\n| Risk | Higher | Lower |\n| Priority in Bankruptcy | Last | Before Common |\n| Typical Investors | Retail, Growth-focused | Income-focused |\n\n## How Stocks are Priced\n\nStock prices are determined by:\n\n1. **Supply and Demand:**\n   - More buyers → Price goes up\n   - More sellers → Price goes down\n\n2. **Company Performance:**\n   - Earnings reports\n   - Revenue growth\n   - Profit margins\n\n3. **Market Sentiment:**\n   - Investor confidence\n   - Economic outlook\n   - Industry trends\n\n4. **External Factors:**\n   - Interest rates\n   - Economic data\n   - Geopolitical events\n\n## Stock Symbols (Tickers)\n\nEvery publicly traded stock has a unique ticker symbol:\n\n- **AAPL** - Apple Inc.\n- **MSFT** - Microsoft Corporation\n- **GOOGL** - Alphabet (Google) Class A\n- **ASML** - ASML Holding (Dutch semiconductor)\n- **GLPG** - Galapagos NV (Belgian biotech)\n\n## Dividends Explained\n\n**Dividend:** Portion of company profits distributed to shareholders\n\n**Dividend Yield Formula:**\n```\nDividend Yield = (Annual Dividend Per Share / Stock Price) × 100%\n```\n\n**Example:**\nStock Price: $100\nAnnual Dividend: $4\nDividend Yield = ($4 / $100) × 100% = 4%\n\n**Types of Companies:**\n- **Dividend Aristocrats:** Increase dividends for 25+ consecutive years\n- **Growth Companies:** Reinvest profits instead of paying dividends (like Amazon, Tesla)\n- **Income Stocks:** Focus on high, stable dividends (like utilities, telecom)\n\n## Stock Splits\n\n**What is a Stock Split?**\nCompany increases number of shares, decreasing price per share proportionally.\n\n**Example: 2-for-1 Split**\n- Before: Own 10 shares at $200/share = $2,000 value\n- After: Own 20 shares at $100/share = $2,000 value\n\n**Why do splits happen?**\n- Make shares more affordable\n- Increase liquidity\n- Psychological appeal\n\n**Note:** Your total investment value doesn''t change!\n\n## Key Takeaways\n\n✅ Stocks represent ownership in a company\n\n✅ Common stock has voting rights, preferred stock has fixed dividends\n\n✅ Stock prices are determined by supply and demand\n\n✅ Dividends provide income, but not all stocks pay them\n\n✅ Stock splits don''t change your investment value\n\n✅ Understanding stock basics is essential for successful trading"
            }
        ]
    }'::jsonb,
    20,
    150,
    'beginner',
    '[1, 2]'::jsonb,
    '["stocks", "equity", "ownership", "dividends"]'::jsonb
);

-- Quiz for Lesson 3
INSERT INTO quizzes (lesson_id, questions, passing_score)
VALUES (
    (SELECT lesson_id FROM lessons WHERE lesson_number = 3),
    '[
        {
            "question": "What does owning a stock represent?",
            "type": "multiple_choice",
            "options": [
                "Lending money to a company",
                "Partial ownership in a company",
                "A guarantee of dividends",
                "A fixed-income investment"
            ],
            "correct_answer": 1,
            "explanation": "When you buy stock, you purchase partial ownership (equity) in a company, making you a shareholder with certain rights and potential for profit."
        },
        {
            "question": "What is the main difference between common and preferred stock?",
            "type": "multiple_choice",
            "options": [
                "Preferred stock has voting rights, common does not",
                "Common stock has voting rights and variable dividends, preferred has fixed dividends and usually no voting rights",
                "Common stock is cheaper than preferred stock",
                "There is no significant difference"
            ],
            "correct_answer": 1,
            "explanation": "Common stock typically includes voting rights and variable dividends with higher growth potential, while preferred stock usually has fixed dividends, priority in payouts, but no voting rights."
        },
        {
            "question": "A stock split changes your total investment value.",
            "type": "true_false",
            "correct_answer": false,
            "explanation": "False. A stock split increases the number of shares while proportionally decreasing the price per share. Your total investment value remains the same."
        },
        {
            "question": "If a stock costs $100 and pays an annual dividend of $5, what is the dividend yield?",
            "type": "multiple_choice",
            "options": [
                "2%",
                "5%",
                "10%",
                "20%"
            ],
            "correct_answer": 1,
            "explanation": "Dividend Yield = (Annual Dividend / Stock Price) × 100% = ($5 / $100) × 100% = 5%"
        },
        {
            "question": "What determines stock prices?",
            "type": "multiple_choice",
            "options": [
                "Only company performance",
                "Only supply and demand",
                "Supply and demand, company performance, market sentiment, and external factors",
                "Government regulations"
            ],
            "correct_answer": 2,
            "explanation": "Stock prices are influenced by multiple factors including supply and demand dynamics, company performance, investor sentiment, economic conditions, and various external factors."
        }
    ]'::jsonb,
    70
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Module 1 lessons 1-3 seeded successfully!';
    RAISE NOTICE 'Created 3 lessons with quizzes';
    RAISE NOTICE 'Total XP available: 350 XP';
END $$;
