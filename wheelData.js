/* ==========================================================================
   DAILY LUCKY WHEEL DATA - REWARDS LIST
   ========================================================================== */

export const wheelRewards = [
    {
        id: 0,
        type: 'coins',
        amount: 2000,
        rarity: 'epic',
        weight: 15,
        emoji: '💰',
        nameEN: '2,000 Coins',
        nameTH: '2,000 เหรียญ'
    },
    {
        id: 1,
        type: 'xp',
        amount: 150,
        rarity: 'common',
        weight: 25,
        emoji: '⭐',
        nameEN: '150 XP Boost',
        nameTH: '150 โบนัส XP'
    },
    {
        id: 2,
        type: 'gems',
        amount: 50,
        rarity: 'rare',
        weight: 20,
        emoji: '💎',
        nameEN: '50 Gems',
        nameTH: '50 เจ็ม'
    },
    {
        id: 3,
        type: 'energy',
        amount: 2,
        rarity: 'common',
        weight: 20,
        emoji: '⚡',
        nameEN: '2 Energy Refuel',
        nameTH: '2 พลังงาน'
    },
    {
        id: 4,
        type: 'fragment',
        amount: 3,
        rarity: 'epic',
        weight: 10,
        emoji: '🐹',
        nameEN: '3 Character Shards',
        nameTH: 'ชิ้นส่วนตัวละคร 3 ชิ้น'
    },
    {
        id: 5,
        type: 'sticker',
        amount: 1,
        rarity: 'legendary',
        weight: 5,
        emoji: '📖',
        nameEN: '1 Sticker Pack',
        nameTH: 'ซองสติกเกอร์ 1 ซอง'
    },
    {
        id: 6,
        type: 'coins',
        amount: 5000,
        rarity: 'legendary',
        weight: 5,
        emoji: '👑',
        nameEN: '5,000 Coins Jackpot',
        nameTH: 'แจ็คพอต 5,000 เหรียญ'
    },
    {
        id: 7,
        type: 'gems',
        amount: 100,
        rarity: 'epic',
        weight: 10,
        emoji: '🔮',
        nameEN: '100 Mega Gems',
        nameTH: '100 เจ็มพิเศษ'
    }
];

export function getRandomReward() {
    const totalWeight = wheelRewards.reduce((sum, r) => sum + r.weight, 0);
    let random = Math.random() * totalWeight;
    for (const reward of wheelRewards) {
        if (random < reward.weight) {
            return reward;
        }
        random -= reward.weight;
    }
    return wheelRewards[0];
}
