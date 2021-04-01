(define (domain blocksworld)
  (:requirements :strips :negative-preconditions :no-duplicates :mep)
  (:predicates (clear ?x) (onTable ?x) (holding ?x) (on ?x ?y) (at ?x ?y) (in ?ag - agent))
 

  (:action putdown
    :parameters (?ag - agent ?ob )
    :precondition (holding ?ob)
    :effect (and (on ?ob ?ob) (when (and (clear ?ob) (not(onTable ?ob))) (and (not (onTable ?ob)) (holding ?ob))) (when(not (clear ?ob)) (not (holding ?ob))))
	:observers (forall (?ag1)(when( not(holding ?ag1))(?ag1)))
	:p_observers (and (when( not(holding ?ob)) (and (?ag ag1 ag2))) (when(holding ?ob)(not (ag3))))

	)
  
)