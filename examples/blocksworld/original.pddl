(define (domain blocksworld)
  (:requirements :strips :negative-preconditions :no-duplicates :mep)
  (:predicates (clear ?x) (onTable ?x) (holding ?x) (on ?x ?y) (at ?x ?y) (in ?ag - agent))
 

  (:action pickup
	:act_type 	sensing
    :parameters (?ag1 - agent ?ob)
    :precondition (and ([?ag1 -agent ]([?ag1]([?ag1]((clear ?ob))))) ([?ag1 ag3](onTable ?ob)))
    :effect (when (holding ?ob) (and (clear ?ob) (not (clear ?ob)) (not (onTable ?ob))))
    :b_effects (when (holding ?ob) (and (clear ?ob) (not (clear ?ob)) (not (onTable ?ob))))
	:observers (when (holding ?ob) (?ag1))
	:p_observers (?ag1)
  )

  (:action putdown
    :parameters (?ob)
    :precondition (holding ?ob)
    :effect (and (clear ?ob) (onTable ?ob) (not (holding ?ob)))
	:observers (forall (?ag1 -agent) (?ag1))
	)
  

  (:action stack
    :parameters (?ag1 - agent ?ob ?underob)
    :precondition (and (clear ?underob) (holding ?ob) (not (equal ?ob ?underob)))
    :effect (and (clear ?ob) (on ?ob ?underob) (not (clear ?underob)) (not (holding ?ob)))
	:observers (?ag1)
  )

  (:action unstack
    :parameters (?ob ?underob)
    :precondition (and (on ?ob ?underob) (clear ?ob) (not (equal ?ob ?underob)))
    :effect (and (holding ?ob) (clear ?underob) (not (on ?ob ?underob)) (not (clear ?ob)))
  )
)