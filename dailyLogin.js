/* ==========================================================================
   DAILY LOGIN SYSTEM CONTROLLER
   ========================================================================== */

import { dailyLoginRewards } from './dailyLoginData.js';

export const DailyLogin = {
    state: null,
    saveProgression: null,
    updateProgressionUI: null,
    addXP: null,
    triggerAlertLog: null,
    triggerConfettiBurst: null,
    triggerMiniGameVictoryJingle: null,
    triggerPurchaseChime: null,
    triggerCoinBurst: null,
    showModal: null,
    hideModal: null,
    awardStickerPack: null,

    init(options) {
        this.state = options.state;
        this.saveProgression = options.saveProgression;
        this.updateProgressionUI = options.updateProgressionUI;
        this.addXP = options.addXP;
        this.triggerAlertLog = options.triggerAlertLog;
        this.triggerConfettiBurst = options.triggerConfettiBurst;
        this.triggerMiniGameVictoryJingle = options.triggerMiniGameVictoryJingle;
        this.triggerPurchaseChime = options.triggerPurchaseChime;
        this.triggerCoinBurst = options.triggerCoinBurst || (() => {});
        this.showModal = options.showModal;
        this.hideModal = options.hideModal;
        this.awardStickerPack = options.awardStickerPack;

        // Attach event listeners
        const claimBtn = document.getElementById('btn-daily-claim');
        if (claimBtn) {
            claimBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.claimReward();
            });
        }

        const lobbyBtn = document.getElementById('btn-open-daily-login');
        if (lobbyBtn) {
            lobbyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showDailyLoginModal();
            });
        }
    },

    checkDailyLogin() {
        if (this.state.attractModeActive) return;

        const today = new Date().toDateString();
        if (!this.state.progression.dailyLogin) {
            this.state.progression.dailyLogin = { lastClaimDate: null, currentDay: 1, claimedToday: false };
        }

        const daily = this.state.progression.dailyLogin;

        // If it's a new day
        if (daily.lastClaimDate !== today) {
            // If the player claimed their previous reward, advance the day.
            // If they didn't claim, they stay on their current unclaimed day.
            if (daily.claimedToday) {
                daily.currentDay = (daily.currentDay % 7) + 1;
                daily.claimedToday = false;
            }
            // Save state immediately
            if (typeof this.saveProgression === 'function') this.saveProgression();
            this.showDailyLoginModal();
        }
    },

    showDailyLoginModal() {
        const daily = this.state.progression.dailyLogin || { lastClaimDate: null, currentDay: 1, claimedToday: false };
        this.renderDailyLoginGrid(daily.currentDay, daily.claimedToday);

        // Adjust Claim Button status
        const claimBtn = document.getElementById('btn-daily-claim');
        if (claimBtn) {
            const btnSpan = claimBtn.querySelector('.btn-bubble-content') || claimBtn;
            const isThai = this.state.lang === 'th';
            if (daily.claimedToday) {
                btnSpan.innerText = isThai ? "รับไปแล้ว! ✓" : "CLAIMED TODAY! ✓";
                claimBtn.disabled = true;
                claimBtn.style.opacity = '0.6';
                claimBtn.style.pointerEvents = 'none';
            } else {
                btnSpan.innerText = isThai ? "รับรางวัลวันนี้! 🎁" : "CLAIM TODAY! 🎁";
                claimBtn.disabled = false;
                claimBtn.style.opacity = '1';
                claimBtn.style.pointerEvents = 'auto';
            }
        }

        if (typeof this.showModal === 'function') {
            this.showModal('daily-login-modal');
        } else {
            const modal = document.getElementById('daily-login-modal');
            if (modal) modal.style.display = 'flex';
        }
    },

    renderDailyLoginGrid(currentDay, claimedToday) {
        const grid = document.getElementById('daily-login-grid');
        if (!grid) return;
        grid.innerHTML = '';

        const isThai = this.state.lang === 'th';

        dailyLoginRewards.forEach(r => {
            const card = document.createElement('div');
            card.className = 'daily-login-card';
            
            // Highlight Day 7 as the grand finale
            if (r.day === 7) {
                card.classList.add('day-7-card');
            }

            const isClaimed = r.day < currentDay || (r.day === currentDay && claimedToday);
            const isActive = r.day === currentDay && !claimedToday;

            if (isClaimed) {
                card.classList.add('claimed');
                const stamp = document.createElement('div');
                stamp.className = 'claimed-stamp';
                stamp.innerText = '✓';
                card.appendChild(stamp);
            } else if (isActive) {
                card.classList.add('active');
            } else {
                card.classList.add('locked');
            }

            const rewardName = isThai ? r.nameTH : r.nameEN;

            card.innerHTML += `
                <span class="card-day">DAY ${r.day}</span>
                <span class="card-icon">${r.icon}</span>
                <span class="card-name">${rewardName}</span>
            `;

            grid.appendChild(card);
        });
    },

    claimReward() {
        const daily = this.state.progression.dailyLogin;
        if (!daily || daily.claimedToday) return;

        const today = new Date().toDateString();
        const currentDay = daily.currentDay;
        const r = dailyLoginRewards[currentDay - 1];

        // 1. Apply reward
        const isThai = this.state.lang === 'th';
        let feedbackMessage = '';

        if (r.type === 'coins') {
            this.state.progression.coins = (this.state.progression.coins || 0) + r.amount;
            feedbackMessage = isThai 
                ? ` ได้รับ ${r.amount} เหรียญทอง 💰`
                : ` Received ${r.amount} Coins 💰`;
        } else if (r.type === 'gems') {
            this.state.progression.gems = (this.state.progression.gems || 0) + r.amount;
            feedbackMessage = isThai
                ? ` ได้รับ ${r.amount} เจ็ม 💎`
                : ` Received ${r.amount} Gems 💎`;
        } else if (r.type === 'ticket') {
            this.state.progression.luckyWheelTickets = (this.state.progression.luckyWheelTickets || 0) + r.amount;
            feedbackMessage = isThai
                ? ` ได้รับ ตั๋ววงล้อนำโชค ${r.amount} ใบ 🎟️`
                : ` Received ${r.amount} Lucky Wheel Ticket 🎟️`;
        } else if (r.type === 'sticker_pack') {
            if (typeof this.awardStickerPack === 'function') {
                const sticker = this.awardStickerPack(r.packType);
                if (sticker) {
                    const stickerName = isThai ? sticker.thName : sticker.name;
                    feedbackMessage = isThai
                        ? ` ได้รับสติกเกอร์: ${sticker.icon} ${stickerName}`
                        : ` Unboxed Sticker: ${sticker.icon} ${stickerName}`;
                }
            } else {
                // Fallback to random sticker
                const activeChar = (this.state.players && this.state.players[0] && this.state.players[0].characterType) || 'cat';
                if (typeof window.awardRandomSticker === 'function') {
                    window.awardRandomSticker(activeChar);
                }
                feedbackMessage = isThai ? ` ได้รับซองสติกเกอร์ท่องเที่ยว 📖` : ` Received Travel Sticker Pack 📖`;
            }
        } else if (r.type === 'chest') {
            const chestType = r.chestType || 'epic';
            if (!this.state.progression.chestsOwned) {
                this.state.progression.chestsOwned = { common: 0, rare: 0, epic: 0, legendary: 0 };
            }
            this.state.progression.chestsOwned[chestType] = (this.state.progression.chestsOwned[chestType] || 0) + r.amount;
            feedbackMessage = isThai
                ? ` ได้รับหีบสมบัติ ${chestType.toUpperCase()} 🔮`
                : ` Received ${chestType.toUpperCase()} Treasure Chest 🔮`;
        }

        // Add to reward history
        if (!this.state.progression.rewardHistory) {
            this.state.progression.rewardHistory = [];
        }
        this.state.progression.rewardHistory.push({
            date: today,
            source: 'daily_login',
            day: currentDay,
            rewardType: r.type,
            rewardAmount: r.amount,
            rewardName: r.nameEN
        });

        // 2. Play FX & visual burst
        if (typeof this.triggerPurchaseChime === 'function') this.triggerPurchaseChime();
        if (typeof this.triggerConfettiBurst === 'function') this.triggerConfettiBurst();
        if (typeof this.triggerCoinBurst === 'function') this.triggerCoinBurst();

        // 3. Update claim state
        daily.lastClaimDate = today;
        daily.claimedToday = true;

        // Save progress & refresh HUDs
        if (typeof this.saveProgression === 'function') this.saveProgression();
        if (typeof this.updateProgressionUI === 'function') this.updateProgressionUI();

        // Re-render grid to show claimed state
        this.renderDailyLoginGrid(currentDay, true);

        // Update Claim Button
        const claimBtn = document.getElementById('btn-daily-claim');
        if (claimBtn) {
            const btnSpan = claimBtn.querySelector('.btn-bubble-content') || claimBtn;
            btnSpan.innerText = isThai ? "รับไปแล้ว! ✓" : "CLAIMED TODAY! ✓";
            claimBtn.disabled = true;
            claimBtn.style.opacity = '0.6';
            claimBtn.style.pointerEvents = 'none';
        }

        // 4. Trigger alert log
        if (typeof this.triggerAlertLog === 'function') {
            this.triggerAlertLog(`🎁 ${feedbackMessage}`);
        }

        // 5. Reward Popup animation sequence
        this.showRewardPopup(r);
    },

    showRewardPopup(reward) {
        // Create dynamic overlay popup for reward claim celebration
        const isThai = this.state.lang === 'th';
        const popup = document.createElement('div');
        popup.className = 'daily-reward-celebration-popup';
        popup.style.position = 'fixed';
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%) scale(0.4) rotate(-5deg)';
        popup.style.opacity = '0';
        popup.style.transition = 'transform 0.45s cubic-bezier(0.34, 1.7, 0.64, 1.0), opacity 0.35s ease';
        popup.style.zIndex = '30000';
        popup.style.background = 'radial-gradient(circle, #ffffff 0%, #fffbf0 100%)';
        popup.style.border = '5px solid var(--border-dark)';
        popup.style.borderRadius = '30px';
        popup.style.padding = '30px';
        popup.style.boxShadow = 'var(--toy-shadow-large)';
        popup.style.textAlign = 'center';
        popup.style.fontFamily = 'var(--font-cute)';
        popup.style.display = 'flex';
        popup.style.flexDirection = 'column';
        popup.style.alignItems = 'center';
        popup.style.width = '300px';

        popup.innerHTML = `
            <div style="font-size: 1.1rem; font-weight: 800; color: var(--pastel-pink); text-shadow: 1px 1px 0 var(--border-dark); -webkit-text-stroke: 0.5px var(--border-dark); text-transform: uppercase;">
                ${isThai ? 'ได้รับรางวัลแล้ว!' : 'REWARD CLAIMED!'}
            </div>
            <div class="reward-popup-emoji" style="font-size: 5rem; margin: 15px 0; filter: drop-shadow(0 4px 0 rgba(0,0,0,0.15)); animation: bounce-effect 1s infinite ease-in-out;">
                ${reward.icon}
            </div>
            <div style="font-size: 1.4rem; font-weight: 900; color: var(--text-dark);">
                ${isThai ? reward.nameTH : reward.nameEN}
            </div>
            <button class="cute-action-btn btn-green" style="margin-top: 20px; font-size: 1rem; padding: 6px 20px; box-shadow: 0 4px 0 var(--border-dark);" id="btn-popup-celebrate-close">
                ${isThai ? 'สุดยอด! ✨' : 'AWESOME! ✨'}
            </button>
        `;

        document.body.appendChild(popup);

        // Trigger scale up and fade in transition
        setTimeout(() => {
            popup.style.transform = 'translate(-50%, -50%) scale(1.0) rotate(0deg)';
            popup.style.opacity = '1';
        }, 20);

        // Add bounce-effect style if not already exists
        if (!document.getElementById('daily-popup-anim-style')) {
            const style = document.createElement('style');
            style.id = 'daily-popup-anim-style';
            style.textContent = `
                @keyframes bounce-effect {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-10px); }
                }
            `;
            document.head.appendChild(style);
        }

        const closeBtn = popup.querySelector('#btn-popup-celebrate-close');
        closeBtn.addEventListener('click', () => {
            if (typeof this.triggerPurchaseChime === 'function') this.triggerPurchaseChime();
            popup.remove();
            
            // Hide the main daily login modal after celebration close
            if (typeof this.hideModal === 'function') {
                this.hideModal('daily-login-modal');
            }
            const modal = document.getElementById('daily-login-modal');
            if (modal) modal.style.display = 'none';
        });
    }
};
