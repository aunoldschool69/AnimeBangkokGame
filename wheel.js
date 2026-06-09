/* ==========================================================================
   DAILY LUCKY WHEEL CONTROLLER
   ========================================================================== */

import { wheelRewards, getRandomReward } from './wheelData.js';

export const LuckyWheel = {
    state: null,
    saveProgression: null,
    updateProgressionUI: null,
    addXP: null,
    triggerAlertLog: null,
    triggerConfettiBurst: null,
    triggerMiniGameVictoryJingle: null,
    triggerPurchaseChime: null,
    triggerButtonPressChime: null,
    discoverProperty: null,
    collectionProperties: null,
    characterTemplates: null,
    showModal: null,
    hideModal: null,
    triggerSelectionChime: null,

    isSpinning: false,
    cooldownInterval: null,
    currentRotation: 0,

    init(options) {
        this.state = options.state;
        this.saveProgression = options.saveProgression;
        this.updateProgressionUI = options.updateProgressionUI;
        this.addXP = options.addXP;
        this.triggerAlertLog = options.triggerAlertLog;
        this.triggerConfettiBurst = options.triggerConfettiBurst;
        this.triggerMiniGameVictoryJingle = options.triggerMiniGameVictoryJingle;
        this.triggerPurchaseChime = options.triggerPurchaseChime;
        this.triggerButtonPressChime = options.triggerButtonPressChime;
        this.discoverProperty = options.discoverProperty;
        this.collectionProperties = options.collectionProperties;
        this.characterTemplates = options.characterTemplates;
        this.showModal = options.showModal;
        this.hideModal = options.hideModal;
        this.triggerSelectionChime = options.triggerSelectionChime || (() => {});

        // Render the wheel SVG
        const plate = document.getElementById('lucky-wheel-plate');
        if (plate) {
            plate.innerHTML = this.generateWheelSVG();
        }

        // Set up button listeners
        const openBtn = document.getElementById('btn-open-lucky-wheel');
        if (openBtn) {
            openBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof this.triggerButtonPressChime === 'function') this.triggerButtonPressChime();
                this.openWheelModal();
            });
        }

        const closeBtn = document.getElementById('btn-close-lucky-wheel');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.isSpinning) return;
                if (typeof this.triggerButtonPressChime === 'function') this.triggerButtonPressChime();
                this.hideModal('lucky-wheel-modal');
                const modal = document.getElementById('lucky-wheel-modal');
                if (modal) modal.style.display = 'none';
            });
        }

        const spinBtn = document.getElementById('btn-lucky-spin');
        if (spinBtn) {
            spinBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.spin();
            });
        }

        const claimRewardBtn = document.getElementById('btn-lucky-reward-claim');
        if (claimRewardBtn) {
            claimRewardBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof this.triggerButtonPressChime === 'function') this.triggerButtonPressChime();
                this.hideModal('lucky-reward-modal');
                const modal = document.getElementById('lucky-reward-modal');
                if (modal) modal.style.display = 'none';
            });
        }

        // Listen for CSS transition end to resolve reward
        if (plate) {
            plate.addEventListener('transitionend', () => {
                this.onSpinComplete();
            });
        }

        // Start cooldown countdown timer updates
        this.startCooldownTimer();
    },

    generateWheelSVG() {
        const R = 135;
        const CX = 145;
        const CY = 145;
        const numWedges = wheelRewards.length;
        const anglePerWedge = 360 / numWedges; // 45

        const rarityColors = {
            common: '#e0f2fe',     // pastel blue
            rare: '#dbeafe',       // pastel royal blue
            epic: '#e9d5ff',       // pastel purple
            legendary: '#fef9c3'   // pastel gold
        };

        let svgContent = `
            <svg viewBox="0 0 290 290" width="100%" height="100%">
                <!-- Outer rim -->
                <circle cx="${CX}" cy="${CY}" r="138" fill="var(--ct2-ink)" />
                <circle cx="${CX}" cy="${CY}" r="134" fill="#f8fafc" stroke="var(--ct2-ink)" stroke-width="4" />
        `;

        // Draw wedges
        for (let i = 0; i < numWedges; i++) {
            const reward = wheelRewards[i];
            const startAngle = i * anglePerWedge - 22.5;
            const endAngle = (i + 1) * anglePerWedge - 22.5;

            const startRad = (startAngle * Math.PI) / 180;
            const endRad = (endAngle * Math.PI) / 180;

            const x1 = CX + R * Math.cos(startRad);
            const y1 = CY + R * Math.sin(startRad);
            const x2 = CX + R * Math.cos(endRad);
            const y2 = CY + R * Math.sin(endRad);

            const color = rarityColors[reward.rarity] || '#ffffff';

            svgContent += `
                <path d="M ${CX} ${CY} L ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2} Z" 
                      fill="${color}" stroke="var(--ct2-ink)" stroke-width="3" />
            `;
        }

        // Draw labels and icons
        for (let i = 0; i < numWedges; i++) {
            const reward = wheelRewards[i];
            const midAngle = i * anglePerWedge;
            const midRad = (midAngle * Math.PI) / 180;

            // Radius position inside wedge
            const textR = 85;
            const tx = CX + textR * Math.cos(midRad);
            const ty = CY + textR * Math.sin(midRad);

            const textRotation = midAngle + 90; // Rotate labels radially

            const isThai = this.state && this.state.lang === 'th';
            let label = reward.type === 'coins' ? `${reward.amount}`
                      : reward.type === 'gems' ? `${reward.amount}`
                      : reward.type === 'xp' ? `${reward.amount} XP`
                      : reward.type === 'energy' ? `+${reward.amount}`
                      : reward.type === 'sticker' ? (isThai ? 'สติกเกอร์' : 'Sticker')
                      : (isThai ? 'ชิ้นส่วน' : 'Shard');

            svgContent += `
                <g transform="translate(${tx}, ${ty}) rotate(${textRotation})">
                    <text x="0" y="-12" text-anchor="middle" dominant-baseline="middle" font-family="var(--font-cute)" font-size="22" font-weight="900" fill="var(--ct2-ink)" stroke="white" stroke-width="2" paint-order="stroke fill">${reward.emoji}</text>
                    <text x="0" y="10" text-anchor="middle" dominant-baseline="middle" font-family="var(--font-cute)" font-size="9.5" font-weight="900" fill="var(--ct2-ink)" stroke="white" stroke-width="2" paint-order="stroke fill">${label}</text>
                </g>
            `;
        }

        // Draw 24 marquee bulbs along the rim
        const numBulbs = 24;
        for (let j = 0; j < numBulbs; j++) {
            const bulbAngle = j * (360 / numBulbs);
            const bulbRad = (bulbAngle * Math.PI) / 180;
            const bx = CX + 130 * Math.cos(bulbRad);
            const by = CY + 130 * Math.sin(bulbRad);
            const bulbClass = j % 2 === 0 ? 'lucky-wheel-bulb-odd' : 'lucky-wheel-bulb-even';

            svgContent += `
                <circle cx="${bx}" cy="${by}" r="3.5" class="${bulbClass}" fill="#fde047" stroke="var(--ct2-ink)" stroke-width="1.5" />
            `;
        }

        svgContent += `</svg>`;
        return svgContent;
    },

    openWheelModal() {
        this.showModal('lucky-wheel-modal');
        const modal = document.getElementById('lucky-wheel-modal');
        if (modal) modal.style.display = 'flex';
        this.updateSpinButtonState();
    },

    checkCooldown() {
        if (!this.state || !this.state.progression || !this.state.progression.luckyWheel) {
            return { available: true, timeRemaining: 0 };
        }
        const lastSpin = this.state.progression.luckyWheel.lastSpinTime;
        if (!lastSpin) {
            return { available: true, timeRemaining: 0 };
        }

        const now = Date.now();
        const cooldownMs = 24 * 60 * 60 * 1000; // 24 hours
        const elapsed = now - lastSpin;
        const remaining = cooldownMs - elapsed;

        // QA Bypass: If qa_simulate url flag is active, bypass cooldown or make it 10 seconds
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('qa_simulate')) {
            return { available: elapsed >= 10000, timeRemaining: Math.max(0, 10000 - elapsed) };
        }

        return {
            available: remaining <= 0,
            timeRemaining: Math.max(0, remaining)
        };
    },

    startCooldownTimer() {
        if (this.cooldownInterval) clearInterval(this.cooldownInterval);
        this.cooldownInterval = setInterval(() => {
            this.updateSpinButtonState();
        }, 1000);
    },

    updateSpinButtonState() {
        const spinBtn = document.getElementById('btn-lucky-spin');
        if (!spinBtn) return;

        const { available, timeRemaining } = this.checkCooldown();
        const tickets = this.state && this.state.progression ? (this.state.progression.luckyWheelTickets || 0) : 0;
        const isThai = this.state && this.state.lang === 'th';

        if (this.isSpinning) {
            spinBtn.disabled = true;
            spinBtn.style.opacity = '0.7';
            const span = spinBtn.querySelector('.btn-bubble-content');
            if (span) span.innerText = isThai ? "กำลังสุ่ม... 🎡" : "SPINNING... 🎡";
            return;
        }

        if (available) {
            spinBtn.disabled = false;
            spinBtn.style.opacity = '1';
            spinBtn.style.pointerEvents = 'auto';
            const span = spinBtn.querySelector('.btn-bubble-content');
            if (span) span.innerText = isThai ? "หมุนฟรีเลย! 🎁" : "SPIN FOR FREE! 🎁";
        } else if (tickets > 0) {
            spinBtn.disabled = false;
            spinBtn.style.opacity = '1';
            spinBtn.style.pointerEvents = 'auto';
            const span = spinBtn.querySelector('.btn-bubble-content');
            if (span) span.innerText = isThai ? `หมุนด้วยตั๋ว! 🎟️ (${tickets} ใบ)` : `SPIN WITH TICKET! 🎟️ (${tickets} left)`;
        } else {
            spinBtn.disabled = true;
            spinBtn.style.opacity = '0.6';
            spinBtn.style.pointerEvents = 'none';
            const span = spinBtn.querySelector('.btn-bubble-content');

            // Format countdown time
            const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
            const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);

            const pad = (num) => String(num).padStart(2, '0');
            const timerStr = `${pad(hours)}h ${pad(minutes)}m ${pad(seconds)}s`;

            if (span) span.innerText = isThai ? `รออีก: ${timerStr} ⏳` : `COOLDOWN: ${timerStr} ⏳`;
        }
    },

    spin() {
        const { available } = this.checkCooldown();
        const tickets = this.state && this.state.progression ? (this.state.progression.luckyWheelTickets || 0) : 0;
        
        if ((!available && tickets <= 0) || this.isSpinning) return;

        this.usedTicketForSpin = false;
        if (!available && tickets > 0) {
            this.usedTicketForSpin = true;
            this.state.progression.luckyWheelTickets--;
            if (typeof this.saveProgression === 'function') this.saveProgression();
            if (typeof this.updateProgressionUI === 'function') this.updateProgressionUI();
        }

        this.isSpinning = true;
        this.updateSpinButtonState();

        const closeBtn = document.getElementById('btn-close-lucky-wheel');
        if (closeBtn) closeBtn.style.pointerEvents = 'none';

        // Select reward
        this.winningReward = getRandomReward();
        console.log("Lucky Wheel: Winning reward picked: ", this.winningReward);

        const plate = document.getElementById('lucky-wheel-plate');
        if (!plate) return;

        // Math for rotation:
        // Wedge 0 at 3 o'clock initially, but pointer is at 12 o'clock (270deg).
        // Rotate the wheel clockwise so the winning wedge lands at 12 o'clock.
        // targetAngle = 360 * rotations + 270 - (wedgeIndex * 45)
        const rotations = 6;
        const index = this.winningReward.id;
        const targetAngle = (360 * rotations) + 270 - (index * 45) + (Math.random() * 20 - 10);
        this.currentRotation = targetAngle;

        // Apply style transitions
        plate.style.transition = 'transform 6s cubic-bezier(0.15, 0.85, 0.3, 1)';
        plate.style.transform = `rotate(${targetAngle}deg)`;

        // Play slowed down ticking sound effects mimicking mechanical peg clicking
        let tickDelay = 80;
        let tickElapsed = 0;
        const animateTicks = () => {
            if (tickElapsed < 5500 && this.isSpinning) {
                if (typeof this.triggerSelectionChime === 'function') {
                    this.triggerSelectionChime();
                }
                
                const pointer = document.querySelector('.lucky-wheel-pointer');
                if (pointer) {
                    pointer.classList.remove('clicking');
                    void pointer.offsetWidth; // Force reflow
                    pointer.classList.add('clicking');
                }

                tickDelay = tickDelay * 1.14; // Exponentially slow down
                tickElapsed += tickDelay;
                setTimeout(animateTicks, tickDelay);
            }
        };
        setTimeout(animateTicks, tickDelay);
    },

    onSpinComplete() {
        this.isSpinning = false;

        const closeBtn = document.getElementById('btn-close-lucky-wheel');
        if (closeBtn) closeBtn.style.pointerEvents = 'auto';

        // Reset plate rotation back into standard range [0, 360) silently
        const plate = document.getElementById('lucky-wheel-plate');
        if (plate) {
            const finalAngleNormalized = this.currentRotation % 360;
            plate.style.transition = 'none';
            plate.style.transform = `rotate(${finalAngleNormalized}deg)`;
        }

        // Set cooldown timestamp only if we did not spin with a ticket
        if (!this.usedTicketForSpin) {
            if (!this.state.progression.luckyWheel) {
                this.state.progression.luckyWheel = { lastSpinTime: null };
            }
            this.state.progression.luckyWheel.lastSpinTime = Date.now();
        }

        // Hide the wheel modal first to avoid overlapping modal lock
        if (typeof this.hideModal === 'function') {
            this.hideModal('lucky-wheel-modal');
        }
        const wheelModal = document.getElementById('lucky-wheel-modal');
        if (wheelModal) wheelModal.style.display = 'none';

        // Distribute the reward and trigger celebratory audio/FX
        this.distributeReward(this.winningReward);

        // Save progress & refresh UI
        if (typeof this.saveProgression === 'function') this.saveProgression();
        if (typeof this.updateProgressionUI === 'function') this.updateProgressionUI();

        this.updateSpinButtonState();
    },

    distributeReward(reward) {
        const isThai = this.state && this.state.lang === 'th';
        let rewardNameText = isThai ? reward.nameTH : reward.nameEN;
        let detailsHtml = '';

        // 1. Process reward modifications in progression state
        if (reward.type === 'coins') {
            this.state.progression.coins = (this.state.progression.coins || 0) + reward.amount;
        } 
        else if (reward.type === 'gems') {
            this.state.progression.gems = (this.state.progression.gems || 0) + reward.amount;
        } 
        else if (reward.type === 'energy') {
            this.state.progression.energy = Math.min(5, (this.state.progression.energy || 0) + reward.amount);
        } 
        else if (reward.type === 'xp') {
            if (typeof this.addXP === 'function') {
                this.addXP(reward.amount);
            } else {
                this.state.progression.totalXp = (this.state.progression.totalXp || 0) + reward.amount;
            }
        } 
        else if (reward.type === 'sticker') {
            const activeChar = (this.state.players && this.state.players[0] && this.state.players[0].characterType) || 'cat';
            if (typeof window.awardRandomSticker === 'function') {
                const won = window.awardRandomSticker(activeChar);
                if (won) {
                    const stickerLabel = isThai ? won.thName : won.name;
                    if (won.isDuplicate) {
                        rewardNameText = isThai
                            ? `ชดเชยสติกเกอร์ซ้ำ: 💰200`
                            : `Duplicate Sticker Refund: 💰200`;
                    } else {
                        rewardNameText = isThai 
                            ? `สติกเกอร์ใหม่: ${won.icon} ${stickerLabel} (ระดับ ${won.level})`
                            : `New Sticker: ${won.icon} ${stickerLabel} (Lv.${won.level})`;
                    }
                }
            }
        } 
        else if (reward.type === 'fragment') {
            const allCharTypes = Object.keys(this.state.progression.characterFragments || {});
            const unlockedList = this.state.progression.unlockedCharacters || ['cat'];
            const lockedList = allCharTypes.filter(c => !unlockedList.includes(c));

            // Select a locked character fragment if possible, otherwise any
            const targetCharType = lockedList.length > 0 
                ? lockedList[Math.floor(Math.random() * lockedList.length)] 
                : allCharTypes[Math.floor(Math.random() * allCharTypes.length)];

            if (targetCharType) {
                if (!this.state.progression.characterFragments) {
                    this.state.progression.characterFragments = {};
                }
                this.state.progression.characterFragments[targetCharType] = 
                    (this.state.progression.characterFragments[targetCharType] || 0) + reward.amount;

                const charTemp = this.characterTemplates.find(t => t.type === targetCharType) || { name: targetCharType, thName: targetCharType, emoji: '🐹' };
                const totalFrags = this.state.progression.characterFragments[targetCharType];
                const charName = isThai ? charTemp.thName : charTemp.name;

                rewardNameText = isThai
                    ? `ชิ้นส่วนตัวละคร ${charTemp.emoji} ${charName} x${reward.amount}`
                    : `Character Fragments: ${charTemp.emoji} ${charName} Shards x${reward.amount}`;

                // Check for immediate character unlocking!
                if (totalFrags >= 10 && !unlockedList.includes(targetCharType)) {
                    unlockedList.push(targetCharType);
                    this.state.progression.unlockedCharacters = unlockedList;

                    setTimeout(() => {
                        if (typeof this.triggerAlertLog === 'function') {
                            this.triggerAlertLog(isThai
                                ? `🎉 ยอดเยี่ยม! สะสมชิ้นส่วนครบ 10 ชิ้นแล้ว! คุณปลดล็อก ${charName} เรียบร้อยแล้ว! 🐹✨`
                                : `🎉 AWESOME! 10 Shards completed! You successfully unlocked ${charName}! 🐹✨`
                            );
                        }
                        if (typeof this.triggerConfettiBurst === 'function') this.triggerConfettiBurst();
                        if (typeof this.triggerMiniGameVictoryJingle === 'function') this.triggerMiniGameVictoryJingle();
                    }, 1500);

                    rewardNameText += isThai 
                        ? ` (ปลดล็อกแล้ว! 🎉)` 
                        : ` (UNLOCKED! 🎉)`;
                } else {
                    rewardNameText += isThai 
                        ? ` (${totalFrags}/10 ชิ้น)` 
                        : ` (${totalFrags}/10 Shards)`;
                }
            }
        }

        // 2. Play synthesized celebratory FX
        if (typeof this.triggerPurchaseChime === 'function') this.triggerPurchaseChime();
        if (typeof this.triggerConfettiBurst === 'function') this.triggerConfettiBurst();
        if (typeof this.triggerAlertLog === 'function') {
            this.triggerAlertLog(isThai 
                ? `🎉 ยินดีด้วย! คุณได้รับ ${rewardNameText} จากการหมุนวงล้อรายวัน!`
                : `🎉 Congratulations! You won ${rewardNameText} from the Daily Lucky Wheel!`
            );
        }

        // 3. Populate Reward Popup
        const iconEl = document.getElementById('lucky-reward-icon');
        const nameEl = document.getElementById('lucky-reward-name');
        const rarityEl = document.getElementById('lucky-reward-rarity');

        if (iconEl) iconEl.innerText = reward.emoji;
        if (nameEl) nameEl.innerText = rewardNameText;
        if (rarityEl) {
            rarityEl.className = `rarity-pill ${reward.rarity}`;
            rarityEl.innerText = reward.rarity.toUpperCase();
        }

        // 4. Show Reward Popup overlay
        this.showModal('lucky-reward-modal');
        const modal = document.getElementById('lucky-reward-modal');
        if (modal) modal.style.display = 'flex';
    }
};
