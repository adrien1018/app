import React from "react"

import {useLocation} from "react-router-dom"

import {SeriesCardProps, Analysis} from "../../types"
import {BasicSparkLines, BasicView} from "../../../components/charts/card"
import {Cache} from "../../common"
import {SeriesCache, SeriesPreferenceCache, ComputerStatusCache} from "../../../cache/cache"

const TITLE = 'Memory'
const URL = 'memory'

class MemoryAnalysisCache extends SeriesCache {
    constructor(uuid: string, statusCache: ComputerStatusCache) {
        super(uuid, 'memory', statusCache)
    }
}


class MemoryPreferenceCache extends SeriesPreferenceCache {
    constructor(uuid: string) {
        super(uuid, 'memory')
    }
}


let cache = new Cache('computer',MemoryAnalysisCache, MemoryPreferenceCache)


function AnalysisSummary(props: SeriesCardProps) {
    return <BasicSparkLines title={TITLE}
                            url={URL}
                            cache={cache}
                            uuid={props.uuid}
                            ref={props.refreshRef}
                            isChartView={true}
                            width={props.width}/>
}

function AnalysisDetails() {
    const location = useLocation()

    return <BasicView title={TITLE}
                      cache={cache}
                      location={location}/>
}


let MemoryAnalysis: Analysis = {
    card: AnalysisSummary,
    view: AnalysisDetails,
    route: `${URL}`
}

export default MemoryAnalysis
