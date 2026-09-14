module EvidenceLifecycle {
  var revision: int
  var verifiedRevision: int
  var passed: bool
  var intact: bool
  var accepted: bool

  action init = all {
    revision' = 0,
    verifiedRevision' = -1,
    passed' = false,
    intact' = true,
    accepted' = false,
  }

  action edit = all {
    revision < 2,
    revision' = revision + 1,
    verifiedRevision' = verifiedRevision,
    passed' = passed,
    intact' = intact,
    accepted' = false,
  }

  action verifyPass = all {
    revision' = revision,
    verifiedRevision' = revision,
    passed' = true,
    intact' = true,
    accepted' = false,
  }

  action verifyFail = all {
    revision' = revision,
    verifiedRevision' = revision,
    passed' = false,
    intact' = true,
    accepted' = false,
  }

  action tamper = all {
    revision' = revision,
    verifiedRevision' = verifiedRevision,
    passed' = passed,
    intact' = false,
    accepted' = false,
  }

  action acceptEvidence = all {
    revision' = revision,
    verifiedRevision' = verifiedRevision,
    passed' = passed,
    intact' = intact,
    accepted' = passed and intact and verifiedRevision == revision,
  }

  action step = any { edit, verifyPass, verifyFail, tamper, acceptEvidence }
  val acceptedIsCurrent = accepted.implies(passed and intact and verifiedRevision == revision)
  run acceptanceTest = init.then(verifyPass).then(acceptEvidence).expect(accepted)
}
