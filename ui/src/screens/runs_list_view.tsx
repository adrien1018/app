import React, {useEffect, useState} from "react"

import {Alert} from "react-bootstrap"
import NETWORK from '../network'
import {RunsList} from "../components/runs_list"
import {Code} from "../components/code"
import {LabLoader} from "../components/loader"
import {Run} from "../components/models"


function RunsListView() {
    const [isLoading, setIsLoading] = useState(true)
    const [networkError, setNetworkError] = useState(null)
    const [runs, setRuns] = useState<Run[]>([])
    const [labMlToken, setLabMlToken] = useState('')

    useEffect(() => {
        NETWORK.get_runs()
            .then((res) => {
                if (res) {
                    setRuns(res.data.runs)
                    setLabMlToken(res.data.labml_token)
                    setIsLoading(false)
                }
            })
            .catch((err) => {
                setNetworkError(err.message)
            })
    })

    useEffect(() => {
        document.title = "LabML: Runs list"
    }, [labMlToken])

    return <div>
        {(() => {
            if (networkError != null) {
                return <Alert variant={'danger'}>{networkError}</Alert>
            } else if (isLoading) {
                return <LabLoader isLoading={isLoading}/>
            } else if (runs.length === 0) {
                return <Code labMlToken={labMlToken}/>
            } else {
                return <RunsList runs={runs}/>
            }
        })()}
    </div>
}

export default RunsListView