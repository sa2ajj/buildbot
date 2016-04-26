:orphan:

=================
Contribution Bits
=================

.. blockdiag::


   blockdiag {
      orientation = portrait;

      new_pr -> quick_review -> for_eight -> myarea -> review -> serious_concerns -> requires -> other_problems -> other_concerns -> label_merge_me -> new_pr_done;

      new_pr[shape=flowchart.loopin, label = "New\nPR"];
      new_pr_done[shape = flowchart.loopout, label = "Review\nDone"];

      quick_review[shape=flowchart.input, label="Quick\nReview"];
      review[shape=flowchart.input, label="Focused\nReview"];

      for_eight[shape=diamond, label="Is it for\neight?"];
      nine_first[shape=diamond, label="nine first?"];

      myarea[shape=diamond, label="Comfortable?"];

      serious_concerns[shape=diamond, label="Serious\nConcerns?"];
      requires[shape=diamond, label="Required\nbits\nMissing?"];
      other_problems[shape=diamond, label="Other\nProblems?"];
      other_concerns[shape=diamond, label="Other\nConcerns?"];

      # updated_pr -> review;

      for_eight -> label_eight -> nine_first -> review;
      nine_first -> label_nine_first[label="yes"];
      label_nine_first -> new_pr_done;

      myarea -> label_please_review[label="no"];
      label_please_review -> new_pr_done;
      serious_concerns -> describe_reason -> label_to_reject[label="yes"];
      label_to_reject -> new_pr_done;
      requires -> label_needs_tests, label_needs_docs, label_needs_relnotes[label="yes"];
      label_needs_tests -> other_problems;
      label_needs_docs -> other_problems;
      label_needs_relnotes -> other_problems;

      other_problems -> label_needs_work[label="yes"];
      label_needs_work -> other_concerns;
      other_concerns -> express_concerns[label="yes"];
      express_concerns -> label_needs_reply;
      label_needs_reply -> new_pr_done;

      labelled_pr -> updated_recently -> has_needed_something;
      labelled_pr[shape=flowchart.loopin, label="Labelled\nPR"];

      updated_pr -> yay;
      updated_pr[shape=flowchart.loopin, label="Updated\nPR"];

      describe_reason[shape=flowchart.input, label="Describe\nReason"];
      express_concerns[shape=flowchart.input, label="Express\nConcerns"];

      # {{{ all labels
      # * must be after all other blocks
      # * colours should be the same as on github
      label_please_review[shape=note, label="Label\n'please review'", color="#bfe5bf"];
      label_merge_me[shape=note, label="Label\n'merge me'", color="#009800"];

      label_needs_tests[shape=note, label="Label\n'needs tests'", color="#f7c6c7"];
      label_needs_docs[shape=note, label="Label\n'needs docs'", color="#f7c6c7"];
      label_needs_relnotes[shape=note, label="Label\n'needs relnotes'", color="#f7c6c7"];
      label_needs_work[shape=note, label="Label\n'needs work'", color="#f7c6c7"];
      label_needs_rebase[shape=note, label="Label\n'needs rebase'", color="#f7c6c7"];
      label_needs_reply[shape=note, label="Label\n'needs reply'", color="#eb6420"];

      label_nine_first[shape=note, label="Label\n'nine first'", color="#eb6420"];
      label_port_to_eight[shape=note, label="Label\n'port-to-eight'", color="#009800"];
      label_eight[shape=note, label="Label\n'eight'", color="#d4c5f9"];

      label_stalled[shape=note, label="Label\n'stalled'", color="#222222", textcolor="#FFFFFF"];

      label_rfc[shape=note, label="Label\n'REF'", color="#bfe5bf"];

      label_do_not_merge[shape=note, label="Label\n'Do Not Merge'", color="#e11d21"];
      label_to_reject[shape=note, label="Label\n'To Reject?'", color="#e11d21"];
      # }}}
    }
