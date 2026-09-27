# The sixteen controls, explained simply

A **control** is a simpler way to score a protein pair. It helps us understand
how much of the main model's performance could come from simple patterns—such
as protein popularity, sequence similarity, or resemblance to previously
recorded interactions.

Think of a protein as a chain of building blocks called **amino acids**,
represented by letters. We want to score a possible interaction between
proteins **A and B**. These are the sixteen controls in the
[study protocol](PROTOCOL.json).

1. **Deterministic hash — a reproducible random score**  
   Assigns every pair a random-looking number, with the same pair always
   receiving the same number. It uses no meaningful biological information.
   This provides a reference for performance expected from chance.

2. **Training degree sum — protein popularity**  
   Scores a pair more highly when its proteins have many recorded interaction
   partners in train2. This tests whether the model benefits simply from
   recognizing proteins that appear frequently in interaction records.

3. **Preferential attachment — both proteins are popular**  
   Multiplies the two proteins' recorded partner counts. This particularly
   favors pairs where **both** proteins have many partners; if either has no
   recorded partners, the score is zero. It tests a more specific version of
   the popularity explanation.

4. **Component degree mass product — popularity of related protein groups**  
   Groups proteins by sequence similarity, adds up the recorded partner counts
   within each group, and combines the totals for A's and B's groups. This
   tests whether belonging to well-represented groups explains the predictions,
   even beyond the individual proteins' popularity.

5. **Training common neighbors — shared partners**  
   Counts how many recorded interaction partners A and B have in common. For
   example, if both interact with C, that contributes one shared partner. This
   tests whether “having mutual friends” is enough to predict an interaction.

6. **Sequence length sum — longer proteins score higher**  
   Uses only the lengths of A and B, giving higher scores to pairs of longer
   proteins. This tests whether differences in protein length can explain
   apparent predictive performance.

7. **Sequence length ratio — similarly sized proteins score higher**  
   Gives higher scores when A and B have similar lengths. Two short proteins
   can therefore score highly, just like two long proteins. This tests whether
   similarity in size is informative.

8. **Within-pair 3-mer cosine — shared short sequence patterns**  
   Counts three-letter patterns in each protein and compares their profiles.
   For example, `ACDEF` contains `ACD`, `CDE`, and `DEF`. This tests whether A
   and B having similar short sequence patterns predicts their interaction.

9. **Exact training interolog, using 3-mers — resemblance to a recorded interacting pair**  
   Searches all recorded train2 interactions X–Y for a pair where A resembles X
   and B resembles Y, using three-letter patterns. Both matches must be good:
   the weaker match limits the score. This tests prediction by analogy to
   previously recorded interactions.

10. **Pooled ESM2 cosine — similarity of AI-generated protein summaries**  
    A pretrained protein AI converts each sequence into a numerical summary,
    or “embedding.” This control compares the summaries of A and B directly.
    It tests whether similarity between these summaries alone explains the
    predictions.

11. **Amino-acid composition cosine — similar ingredients**  
    Compares the relative amounts of each amino acid in A and B, ignoring their
    order completely. Like comparing two recipes by their ingredient
    proportions, it tests whether broad composition is enough.

12. **Interolog using pooled ESM2 — recorded-pair resemblance measured by AI summaries**  
    Uses the same analogy as control 9: A resembles X, B resembles Y, and X–Y
    is a recorded training interaction. Here, resemblance comes from the
    AI-generated summaries. This tests whether transferring known interactions
    through those summaries is sufficient.

13. **Interolog using local alignment — resemblance through matching sequence stretches**  
    Again transfers evidence from recorded X–Y interactions, but measures
    resemblance by lining up matching stretches of amino-acid letters. It
    rewards close matches and penalizes very short matches, while allowing
    much of the proteins to remain unmatched. This tests whether shared
    sequence regions explain the prediction.

14. **Interolog using coverage-aware alignment — matches covering more of the proteins**  
    Similar to control 13, but also rewards matches covering a larger fraction
    of both protein sequences. A small matching region inside two much longer
    proteins receives less credit. This tests a broader form of sequence
    resemblance.

15. **Linear endpoint-only model — learn a separate score for each protein**  
    Learns a simple weighted combination of each protein's AI-generated
    features, producing an individual score for A and another for B. It adds
    those scores. This tests how well individual protein characteristics can
    predict recorded interactions without learning which partners fit together.

16. **Nonlinear endpoint-only model — a more flexible individual-protein score**  
    Uses a small neural network to combine each protein's features more
    flexibly than control 15. It still scores A and B separately and adds
    their scores. This is a stronger test of the same individual-protein
    explanation.

Two distinctions are especially useful when reading the results:

- **Direct similarity versus interaction transfer:** controls 8 and 10 compare
  **A with B**. Controls 9 and 12–14 compare **A with X and B with Y**, where
  **X–Y is a recorded interaction**.
- **Individual scores versus partner compatibility:** controls 15 and 16 can
  learn that certain proteins tend to appear in recorded interactions, but
  their score for A is identical regardless of its proposed partner. That is
  why the partner-swap diagnostic is useful: each protein appears once on
  either side, so these individual contributions cancel.
