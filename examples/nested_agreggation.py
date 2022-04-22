from bson.objectid import ObjectId

aggregation = [
    {'$match': {'submodule': ObjectId('6262d15d0dba8d387633d63d')
        }
    },
    {'$unwind': {'path': '$components', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.components', 'let': {'var': '$components'
            }, 'pipeline': [
                {'$match': {'$expr': {'$eq': ['$_id', '$$var'
                            ]
                        }
                    }
                }
            ], 'as': 'components'
        }
    },
    {'$unwind': {'path': '$components', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.restrictions', 'localField': 'components.restrictions', 'foreignField': '_id', 'as': 'components.restrictions'
        }
    },
    {'$lookup': {'from': 'modules.photo.types', 'localField': 'components.photo_types', 'foreignField': '_id', 'as': 'components.photo_types'
        }
    },
    {'$unwind': {'path': '$components.photo_types', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.components.actions', 'localField': 'components.actions', 'foreignField': '_id', 'as': 'components.actions'
        }
    },
    {'$unwind': {'path': '$components.conditions', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.conditions', 'let': {'var': '$components.conditions'
            }, 'pipeline': [
                {'$match': {'$expr': {'$eq': ['$_id', '$$var'
                            ]
                        }
                    }
                }
            ], 'as': 'components.conditions'
        }
    },
    {'$unwind': {'path': '$components.conditions', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.restrictions', 'localField': 'components.conditions.restrictions', 'foreignField': '_id', 'as': 'components.conditions.restrictions'
        }
    },
    {'$group': {'_id': {'_id': '$_id', 'components': '$components._id'
            }, 'conditions': {'$push': '$components.conditions'
            }, 'doc': {'$first': '$$ROOT'
            }
        }
    },
    {'$replaceRoot': {'newRoot': {'$mergeObjects': ['$doc',
                    {'_id': '$_id'
                    },
                    {'components': {'$mergeObjects': ['$doc.components',
                                {'conditions': '$conditions'
                                }
                            ]
                        }
                    }
                ]
            }
        }
    },
    {'$unwind': {'path': '$components.children', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.components', 'let': {'var': '$components.children'
            }, 'pipeline': [
                {'$match': {'$expr': {'$eq': ['$_id', '$$var'
                            ]
                        }
                    }
                }
            ], 'as': 'components.children'
        }
    },
    {'$unwind': {'path': '$components.children', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.restrictions', 'localField': 'components.children.restrictions', 'foreignField': '_id', 'as': 'components.children.restrictions'
        }
    },
    {'$unwind': {'path': '$components.children.conditions', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.conditions', 'let': {'var': '$components.children.conditions'
            }, 'pipeline': [
                {'$match': {'$expr': {'$eq': ['$_id', '$$var'
                            ]
                        }
                    }
                }
            ], 'as': 'components.children.conditions'
        }
    },
    {'$unwind': {'path': '$components.children.conditions', 'preserveNullAndEmptyArrays': True
        }
    },
    {'$lookup': {'from': 'modules.restrictions', 'localField': 'components.children.conditions.restrictions', 'foreignField': '_id', 'as': 'components.children.conditions.restrictions'
        }
    },
    {'$group': {'_id': {'_id': '$_id', 'components_children': '$components.children._id'
            }, 'conditions': {'$push': '$components.children.conditions'
            }, 'doc': {'$first': '$$ROOT'
            }
        }
    },
    {'$replaceRoot': {'newRoot': {'$mergeObjects': ['$doc',
                    {'_id': '$_id'
                    },
                    {'components': {'$mergeObjects': ['$doc.components',
                                {'children': {'$mergeObjects': ['$doc.components.children',
                                            {'conditions': '$conditions'
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    },
    {'$group': {'_id': {'_id': '$_id._id._id', 'components': '$components._id'
            }, 'children': {'$push': '$components.children'
            }, 'doc': {'$first': '$$ROOT'
            }
        }
    },
    {'$replaceRoot': {'newRoot': {'$mergeObjects': ['$doc',
                    {'_id': '$_id'
                    },
                    {'components': {'$mergeObjects': ['$doc.components',
                                {'children': '$children'
                                }
                            ]
                        }
                    }
                ]
            }
        }
    },
    {'$group': {'_id': '$_id._id', 'components': {'$push': '$components'
            }, 'doc': {'$first': '$$ROOT'
            }
        }
    },
    {'$replaceRoot': {'newRoot': {'$mergeObjects': ['$doc',
                    {'_id': '$_id'
                    },
                    {'components': '$components'
                    }
                ]
            }
        }
    }
]