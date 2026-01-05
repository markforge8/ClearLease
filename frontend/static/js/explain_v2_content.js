/**
 * Explain v2 Content Progressive Disclosure Controller
 * 
 * Phase 1: Auto-show escape_window
 * Phase 2: Show headline on "Show next" click
 * Phase 3: Progressive scroll-triggered disclosure with hard limits
 * Phase 4: Re-centering line after 2-3 items
 */

(function() {
    'use strict';

    // State management
    const state = {
        revealedItems: [],
        lastRevealTime: 0,
        lastScrollPosition: 0,
        scrollDistance: 0,
        itemsRevealed: 0
    };

    // Configuration
    const CONFIG = {
        SCROLL_DISTANCE_THRESHOLD: 300, // pixels
        DWELL_TIME_THRESHOLD: 1000,    // milliseconds
        RECENTERING_AFTER_ITEMS: 2     // Show re-centering after N items
    };

    // Item order (matching data-item attributes)
    const ITEM_ORDER = [
        'escape_window',
        'headline',
        'core_logic',
        'user_actions',
        'recentering',
        'action_translation'
    ];

    /**
     * Initialize: Load data and set up first item
     */
    function init() {
        // Load Explain v2 data (assumed to be passed from backend)
        // For now, using placeholder - should be replaced with actual data injection
        const explainV2Data = window.explainV2Data || getDefaultData();
        
        // Populate content
        populateContent(explainV2Data);
        
        // Phase 1: Auto-show escape_window
        revealItem('escape_window');
        
        // Set up button click handler
        const showNextBtn = document.getElementById('show_next_btn');
        if (showNextBtn) {
            showNextBtn.addEventListener('click', handleShowNext);
        }
        
        // Set up scroll handler for progressive disclosure
        setupScrollHandler();
    }

    /**
     * Populate content from Explain v2 data
     */
    function populateContent(data) {
        // Escape window
        const escapeWindowText = document.getElementById('escape_window_text');
        if (escapeWindowText && data.escape_window) {
            const conditions = data.escape_window.conditions || '';
            escapeWindowText.textContent = conditions || 
                'If you cancel before the specified date, it won\'t automatically renew; if you miss that date, the contract will continue automatically.';
        }

        // Headline
        const headlineText = document.getElementById('headline_text');
        if (headlineText && data.headline) {
            headlineText.textContent = data.headline || 
                'If you miss a specific time point, the cost of exiting later will increase.';
        }

        // Core logic
        const coreLogicText = document.getElementById('core_logic_text');
        if (coreLogicText && data.core_logic) {
            coreLogicText.textContent = data.core_logic || 
                'If you miss a specific time window, the contract will automatically renew, and by then canceling will cost more than it does now.';
        }

        // User actions
        const userActionsList = document.getElementById('user_actions_list');
        if (userActionsList && data.user_actions && Array.isArray(data.user_actions)) {
            userActionsList.innerHTML = '';
            data.user_actions.forEach(action => {
                const li = document.createElement('li');
                li.textContent = action;
                userActionsList.appendChild(li);
            });
        }
    }

    /**
     * Reveal a content item
     */
    function revealItem(itemId) {
        const item = document.querySelector(`[data-item="${itemId}"]`);
        if (!item || state.revealedItems.includes(itemId)) {
            return;
        }

        // Mark as revealed
        state.revealedItems.push(itemId);
        state.itemsRevealed++;
        state.lastRevealTime = Date.now();
        state.lastScrollPosition = window.scrollY || window.pageYOffset;

        // Show item
        item.classList.remove('hidden');
        item.classList.add('visible');

        // Hide pacing brake after headline is revealed
        if (itemId === 'headline') {
            const pacingBrake = document.getElementById('pacing_brake');
            if (pacingBrake) {
                pacingBrake.classList.add('hidden');
            }
        }

        // Check if we should show re-centering line
        if (state.itemsRevealed >= CONFIG.RECENTERING_AFTER_ITEMS) {
            const recenteringItem = document.querySelector('[data-item="recentering"]');
            if (recenteringItem && !state.revealedItems.includes('recentering')) {
                // Show re-centering after a short delay
                setTimeout(() => {
                    revealItem('recentering');
                    // Show Action Translation panel after re-centering (500ms delay)
                    setTimeout(() => {
                        revealItem('action_translation');
                    }, 500);
                }, 500);
            }
        }
    }

    /**
     * Handle "Show next" button click
     */
    function handleShowNext() {
        revealItem('headline');
    }

    /**
     * Setup scroll handler for progressive disclosure
     */
    function setupScrollHandler() {
        let ticking = false;

        function handleScroll() {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    checkScrollTrigger();
                    ticking = false;
                });
                ticking = true;
            }
        }

        window.addEventListener('scroll', handleScroll, { passive: true });
    }

    /**
     * Check if scroll conditions are met for next item reveal
     */
    function checkScrollTrigger() {
        // Only trigger after headline is revealed (Phase 2+)
        if (!state.revealedItems.includes('headline')) {
            return;
        }

        // Calculate scroll distance since last reveal
        const currentScroll = window.scrollY || window.pageYOffset;
        state.scrollDistance += Math.abs(currentScroll - state.lastScrollPosition);
        state.lastScrollPosition = currentScroll;

        // Calculate dwell time
        const dwellTime = Date.now() - state.lastRevealTime;

        // Check if thresholds are met
        const scrollThresholdMet = state.scrollDistance >= CONFIG.SCROLL_DISTANCE_THRESHOLD;
        const dwellThresholdMet = dwellTime >= CONFIG.DWELL_TIME_THRESHOLD;

        if (scrollThresholdMet || dwellThresholdMet) {
            // Find next unrevealed item
            const nextItem = findNextUnrevealedItem();
            // Skip re-centering and action_translation (they are auto-shown)
            if (nextItem && nextItem !== 'recentering' && nextItem !== 'action_translation') {
                revealItem(nextItem);
                // Reset scroll distance after reveal
                state.scrollDistance = 0;
            }
        }
    }

    /**
     * Find next unrevealed item in order
     */
    function findNextUnrevealedItem() {
        for (const itemId of ITEM_ORDER) {
            if (!state.revealedItems.includes(itemId)) {
                return itemId;
            }
        }
        return null;
    }

    /**
     * Default data (fallback if not injected from backend)
     */
    function getDefaultData() {
        return {
            escape_window: {
                conditions: 'If you cancel before the specified date, it won\'t automatically renew; if you miss that date, the contract will continue automatically.'
            },
            headline: 'If you miss a specific time point, the cost of exiting later will increase.',
            core_logic: 'If you miss a specific time window, the contract will automatically renew, and by then canceling will cost more than it does now.',
            user_actions: [
                'Note the deadline for making a decision and set a reminder',
                'Consider whether to continue before the deadline',
                'Find out what the cost would be if you miss the cancellation window'
            ]
        };
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

