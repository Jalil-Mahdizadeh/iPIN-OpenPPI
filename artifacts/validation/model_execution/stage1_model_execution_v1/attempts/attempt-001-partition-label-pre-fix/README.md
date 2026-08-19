# Independent pre-training validation attempt 001

The clean-room validator at producer commit
`4d8c7711dfc8b48b93e19f6c4b6a321ec7969ddc` failed closed with 20 passes,
one failure, and zero warnings. The preserved report SHA-256 is
`6cf273121455abe54377799cfb82db7c604420618d71994e2867f1572352905b`.

The sole failure was a validator schema-key mismatch: it expected the prose
term `protected_test`, while the immutable endpoint-partition artifact uses the
already frozen value `test`. The artifact census itself was correct at 11,900
training, 2,550 development, and 2,550 test endpoints. No production artifact,
embedding, benchmark semantic, partition assignment, or training rule changed.
The validator expectation was corrected before generating authoritative
validation evidence or beginning training.
