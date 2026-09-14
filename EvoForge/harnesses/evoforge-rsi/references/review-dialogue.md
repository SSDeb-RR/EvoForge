# Review dialogue and handoffs

Use this guide to make a manually invoked evolution run conversationally
complete without confusing review, validation, and deployment authority.

## Pending independent evaluation

Explain the gap first:

> The proposal is structurally sound, but it is not behaviorally validated yet.
> The remaining check runs the same scenario with the current and candidate
> skills in separate fresh sessions, then compares the observable decisions.

Then present only the choices that are actually available:

1. **Run fresh A/B evaluation.** Ask: “Would you like me to arrange the fresh
   evaluator runs?” Do this only if the environment permits creating or using
   separate sessions and the user authorizes that work. Keep variants blinded.
2. **Guide user-run evaluation.** Show the packet and manifest locations; say
   the user can run each packet in separate new chats, then provide the
   transcript/session references for recording.
3. **Review the proposal now.** Show the lesson, diff, and packet summary. Say
   this is review only and does not make the proposal deployable.
4. **Leave pending or reject.** Offer explicit rejection only when the user
   wants to stop pursuing the proposal; preserve its reason durably.

Do not ask the user to choose a nonexistent option. If the current environment
cannot run a fresh evaluator, say that plainly and offer the user-run path.

## Evaluator outputs are ready

State that the raw A/B outputs are recorded, then offer to create the reviewer
judgment. The judgment must compare decisions and evidence, not prose quality.
Ask the user to review the proposed judgment if it makes a material call. Once
the helper validates it, report either `approval_ready` or the specific gate
failure.

## Approval-ready proposal

Show the proposal ID, changed sections, validation ID, limitations, and live
target hash. Then ask one explicit question:

> The proposal is approval-ready but has not changed the live skill. Would you
> like me to apply proposal PROPOSAL_ID now?

Only an unambiguous affirmative answer that identifies the proposal (or clearly
refers to the just-presented single proposal) authorizes `apply --approve`.

## Failed or stale proposal

State whether the missing condition is evidence, a regression, a contradiction,
or a changed live target. Offer the smallest next action: revise the candidate,
add or rerun a scenario, restage against the new target, or reject with a
reason. Never silently restage or overwrite the old proposal.
